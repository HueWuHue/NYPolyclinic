class Cart:
    def __init__(self, cart):
        self.__count = 0
        self.__cart = cart

    def get_cart(self):
        return self.__cart

    def set_cart(self, cart):
        self.__cart = cart

    def add(self, item):
        self.get_cart().append(item)

    def remove(self, item):
        new_cart = list()
        item.set_item_want(0)
        for i in self.get_cart():
            if i.get_item_name() != item.get_item_name():
                new_cart.append(i)

        self.set_cart(new_cart)

    def total(self):
        total = 0
        for item in self.get_cart():
            total += item.get_total_price()
        return total

    def clear_cart(self):
        for item in self.get_cart():
            self.remove(item)

    def checkout(self):
        for item in self.get_cart():
            item.set_item_have(item.get_item_have() - item.get_item_want())
        self.clear_cart()

    def get_count(self):
        for item in self.get_cart():
            self.__count += item.get_item_want()
        return self.__count-1

    def check(self, item):
        for i in self.get_cart():
            if i.get_item_name() == item.get_item_name():
                return True

        return False
