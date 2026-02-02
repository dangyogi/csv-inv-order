# rows.py

import math
from collections import namedtuple

from csv_app.row import *
from csv_app.table import Database, set_database_filename

set_database_filename("inv-order.csv")


class CheckInventory(Exception):
    pass


class Items(Row):
    columns = (
        Column("item", required=True),
        Column("unit", required=True),
        Bool_column("perishable", "perish", required=True),
        Column("supplier"),
        Column("supplier_id", "supp_id", parse=int),
        Column("num_per_meal", "#/meal", parse=float),
        Column("num_per_table", "#/table", parse=float),
        Column("num_per_serving", "#/serving", parse=float),
        Column("pkg_size", parse=int, calculated=True),
        Column("pkg_weight", parse=float, calculated=True),
    )
    primary_key = 'item'
    foreign_keys = "Products",

    order_stats_headers = "item unit pkg_size perishable inv uncertainty consumed1 consumed2 " \
                          "min_needed1 max_order min_needed2 min_needed3 order".split()
    order_stats_row_type = namedtuple("order_stats", order_stats_headers)

    @property
    def product(self):
        if self.supplier is None or self.supplier_id is None:
            return None
        return Database.Products[self.item, self.supplier, self.supplier_id]

    @property
    def pkg_size(self):
        if self.product is None:
            return None
        return self.product.pkg_size

    @property
    def pkg_weight(self):
        if self.product is None:
            return None
        return self.product.pkg_weight

    def in_stock(self, verbose=False):
        r'''Return units, uncertainty.

        Does not constrain units to be >= 0.
        '''
        units = 0
        uncertainty = 0
        for inv in Database.Inventory.values():
            if inv.item == self.item:
                match inv.code:
                    case "count":
                        units = inv.total_units
                        uncertainty = inv.uncertainty
                    case "purchased":  # exact count
                        units += inv.total_units
                    case "used":       # may be exact count
                        units -= inv.total_units
                        uncertainty += inv.uncertainty
                    case "consumed":   # estimate
                        units -= inv.total_units
                        uncertainty += inv.uncertainty
                    case "estimate":   # includes uncertainty
                        units = inv.total_units
                        uncertainty = inv.uncertainty
                    case _:
                        raise AssertionError(f"Item({self.item}).in_stock: unknown Inventory.code={inv.code}")
        return units, uncertainty

    def consumed(self, num_served, table_size=6, verbose=False):
        r'''Returns the number of units consumed at breakfast.
        '''
        if self.num_per_serving is not None:
            ans = self.num_per_serving * num_served
            if verbose:
                print(f"{self.item}.consumed: num_per_serving={self.num_per_serving}, {num_served=}, {ans=}")
        elif self.num_per_meal is not None:
            ans = self.num_per_meal
            if verbose:
                print(f"{self.item}.consumed: num_per_meal={self.num_per_meal}, {ans=}")
        elif self.num_per_table is not None:
            tables = round(math.ceil(num_served / table_size))
            ans = self.num_per_table * tables
            if verbose:
                print(f"{self.item}.consumed: num_per_table={self.num_per_table}, {tables=}, {ans=}")
        else:
            ans = 0
            if verbose:
                print(f"{self.item}.consumed: no consumption set, {ans=}")
        return round(ans)

    def order_stats(self, cur_month, table_size=6, override=False, verbose=False):
        r'''Returns order_stats_row_type (stored on this class).
        '''
        def calc_needed(num_servings):
            r'''Calculates total needed to cover num_servings.

            Does not subtract inventory.
            '''
            def print_next(msg):
                if verbose:
                    print(f"{self.item}, {num_servings=}: {msg}")
            needed = 0
            if self.num_per_meal:
                needed = self.num_per_meal
                print_next(f"num_per_meal={self.num_per_meal}")
            elif self.num_per_table:
                tables = int(math.ceil(num_servings / table_size))
                needed = self.num_per_table * tables
                print_next(f"num_per_table={self.num_per_table} * {tables=} == {needed}")
            elif self.num_per_serving:
                needed = self.num_per_serving * num_servings
                print_next(f"num_per_serving={self.num_per_serving} * {num_servings=} == {needed}")
            ans = round(needed)
            if verbose:
                print(f"final needed={ans}")
            return ans

        stats = [self.item, self.unit, self.pkg_size, self.perishable]
        units, uncertainty = self.in_stock(verbose=verbose)  # may be < 0
        if units < 0:
            uncertainty += units  # reduce uncertainty
            if uncertainty < 0:
                uncertainty = 0
            units = 0
        stats.extend((units, uncertainty))


        avg_served1 = Database.Months.avg_meals_served(cur_month.month)
        if cur_month.month == 4:  # Apr
            avg_served2 = 0
        else:
            next_month = Database.Months.inc_month(cur_month.year, cur_month.month)[1]
            avg_served2 = Database.Months.avg_meals_served(next_month)

        consumed1 = self.consumed(cur_month.consumed_fudge * avg_served1, table_size, verbose)
        consumed2 = self.consumed(cur_month.consumed_fudge * avg_served2, table_size, verbose)
        stats.extend((consumed1, consumed2))

        min_needed1 = calc_needed(cur_month.served_fudge * avg_served1)
        stats.append(min_needed1)
        if units - uncertainty >= min_needed1:
            stats.extend((None, None, None, 0))
            return self.order_stats_row_type(*stats)
        min1 = int(math.ceil((min_needed1 - (units - uncertainty)) / self.pkg_size))
        if verbose:
            print(f"{min_needed1=}; in_stock: {units=}, {uncertainty=}; "
                  f"min1 order: {min1}, pkg_size={self.pkg_size}")
        if self.perishable:
            max_order = consumed1 + consumed2
            stats.append(max_order)
            max_limit = int((max_order - (units + uncertainty)) / self.pkg_size)   # floor
            if verbose:
                print(f"{max_order=}, {max_limit=}")
            if max_limit < min1 and not override:
                raise CheckInventory(self.item)
            stats.extend((None, None, round(max(min1, max_limit))))
            return self.order_stats_row_type(*stats)
        # else non_perishable
        stats.append(None)  # max_order
        min_needed2 = calc_needed(cur_month.served_fudge * avg_served2)
        stats.append(min_needed2)
        min2 = int(math.ceil((min_needed2 - (units - uncertainty)) / self.pkg_size))
        if verbose:
            print(f"{min_needed2=}, {min2=}, {consumed1=}")
        if uncertainty > 0.3 * consumed1 and not override:
            raise CheckInventory(self.item)
        min_needed3 = consumed1 + min_needed2
        stats.append(min_needed3)
        min3 = int(math.ceil((min_needed3 - (units - uncertainty)) / self.pkg_size))
        if verbose:
            print(f"{min_needed3=}, {min3=}")
        stats.append(round(max(min1, min2, min3)))
        return self.order_stats_row_type(*stats)

    def order(self, cur_month, table_size=6, override=False, verbose=False):
        r'''Returns how many pkgs to order.
        '''
        return self.order_stats(cur_month, table_size, override, verbose).order

class Products(Row):
    columns = (
        Column("item", required=True),
        Column("supplier", required=True),
        Column("supplier_id", "supp_id", parse=int, default=1),
        Column("name", required=True),
        Column("item_num"),
        Column("location"),
        Column("price", parse=Decimal, required=True),
        Column("pkg_size", "pkg_sz", parse=int),
        Column("pkg_weight", "pkg_wgt", parse=float),
        Column("note"),
        Column("unit", calculated=True),
        Column("price_per_unit", "$/unit", parse=float, calculated=True),
        Column("oz_per_unit", "oz/unit", parse=float, calculated=True),
    )
    primary_keys = "item", "supplier", "supplier_id"
    foreign_keys = "Items",

    @property
    def unit(self):
        return Database.Items[self.item].unit

    @property
    def price_per_unit(self):
        if self.pkg_size is None:
            return None
        return self.price / self.pkg_size

    @property
    def oz_per_unit(self):
        if self.pkg_weight is None or self.pkg_size is None:
            return None
        return self.pkg_weight / self.pkg_size

class Inventory(Row):
    columns = (
        Date_column("date", required=True),
        Column("item", required=True),
        Column("code",
               choices=(
                   "count",
                   "purchased", # exact count
                   "used",      # exact count
                   "consumed",  # estimate
                   "estimate",  # includes uncertainty
               ),
               required=True),
        Column("num_pkgs", parse=float, default=0),
        Column("num_units", parse=int, default=0),
        Column("uncertainty", parse=int, default=0),
        Column("pkg_size", parse=int, calculated=True),
        Column("total_units", parse=float, calculated=True),
    )
    primary_keys = "date item code".split()
    foreign_keys = "Items",

    @property
    def pkg_size(self):
        return Database.Items[self.item].pkg_size

    @property
    def total_units(self):
        return self.num_pkgs * self.pkg_size + self.num_units

class Orders(Row):
    columns = (
        Column("item", required=True),
        Column("qty", parse=int),             # None if no P.O. was created, and purchased_units used.
        Column("supplier"),
        Column("supplier_id", parse=int),
        Column("purchased_pkgs", parse=int),  # if None, defaults to qty
        Column("purchased_units", parse=int), # added to purchased_pkgs
        Column("location"),                   # updates Products if not None
        Column("price", parse=Decimal),       # updates Products if not None
        Column("unit", calculated=True),
        Column("pkg_size", parse=int, calculated=True),
        Column("pkg_weight", parse=float, calculated=True),
    )
    in_database = False
    foreign_keys = "Items", "Products"

    @property
    def item_row(self):
        return Database.Items[self.item]

    @property
    def product(self):
        if self.supplier is None or self.supplier_id is None:
            return self.item_row.product
        return Database.Products[self.item, self.supplier, self.supplier_id]

    @property
    def unit(self):
        return self.item_row.unit

    @property
    def pkg_size(self):
        return self.product.pkg_size

    @property
    def pkg_weight(self):
        return self.product.pkg_weight

class Months(Row):
    columns = (
        Column("month", parse=int, required=True),
        Column("year", parse=int, required=True),
        Date_column("start_date"),
        Date_column("end_date"),
        Column("num_at_meeting", "#@mtg", parse=int),
        Column("staff_at_breakfast", "stf@bf", parse=int),
        Column("tickets_claimed", "tkt_clm", parse=int),
        Column("served_fudge", "srv_fg", parse=float),
        Column("consumed_fudge", "cns_fg", parse=float),
        Column("month_str", "mth_str", calculated=True),
        Column("meals_served", "ml_srv", parse=int, calculated=True),
        Date_column("meeting_date", "mtg_date", calculated=True),
        Date_column("breakfast_date", "bf_date", calculated=True),
    )
   #hidden = frozenset(("month_str", "meeting_date", "breakfast_date"))
    primary_keys = "year", "month"

    @property
    def month_str(self):
        return f"{abbr_month(self.month)} '{str(self.year)[2:]}"

    @property
    def prev_month(self):
        r'''returns (year, month)
        '''
        if self.month == 1:
            return self.year - 1, 12
        return self.year, self.month - 1

    @property
    def meals_served(self):
        if self.staff_at_breakfast is None or self.tickets_claimed is None:
            return None
        return self.staff_at_breakfast + self.tickets_claimed

    @property
    def meeting_date(self):
        return self.nth_day(1, TUESDAY)

    @property
    def breakfast_date(self):
        return self.nth_day(2, SATURDAY)

    def nth_day(self, n, day):
        firstday = date(self.year, self.month, 1).weekday()
        days_to_day = day - firstday
        if days_to_day >= 0:
            ans = date(self.year, self.month, days_to_day + 1 + 7 * (n - 1))
        else:
            ans = date(self.year, self.month, days_to_day + 8 + 7 * (n - 1))
        return ans


# These must be in logical order based on what has to be defined first
Rows = (Items, Products, Inventory, Orders, Months,
)


__all__ = "CheckInventory Decimal date datetime timedelta abbr_month Rows".split()


def run():
    create_database_py(Rows)


if __name__ == "__main__":
    run()

