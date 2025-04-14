import math
from enum import Enum
from typing import List, Tuple
from heapq import heappush, heappop


class OrderStatus(Enum):
    INITIATED = "Initiated"
    ACCEPTED = "Accepted"
    DEPLOYED = "Deployed"
    DELIVERED = "Delivered"


class Location:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance_to(self, other: 'Location') -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class MenuItem:
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price

#Keep items:List[MenuItem] as a nice way to remember the datatype
class Order:
    def __init__(self, order_id: int, customer, restaurant, items: List[MenuItem] , is_priority: bool = False):
        self.order_id = order_id
        self.customer = customer
        self.restaurant = restaurant
        self.items = items
        self.is_priority = is_priority
        self.status = OrderStatus.INITIATED
        self.delivery_agent = None
        self.total_cost = sum(item.price for item in items)
        # Assuming Delivery Fee is a linear function of distance with some base cost c for all orders
        self.delivery_fee = (customer.location.distance_to(restaurant.location) * 0.5)  + 5.0
        if is_priority:
            self.delivery_fee += 5.0

    def update_status(self, new_status: OrderStatus):
        self.status = new_status
        print(f"Order {self.order_id} status updated: {self.status.value}")

class Customer:
    def __init__(self, customer_id: int, name: str, location: Location):
        self.customer_id = customer_id
        self.name = name
        self.location = location
        self.orders = []

    def place_order(self, platform, restaurant, items: List[MenuItem], is_priority: bool = False):
        #order = DeliveryPlatform.create_order(self, restaurant, items, is_priority)
        order = platform.create_order(self, restaurant, items, is_priority)
        self.orders.append(order)
        print(f"Customer {self.name} placed order {order.order_id}")
        return order

    def check_order_status(self, order_id: int):
        for order in self.orders:
            if order.order_id == order_id:
                print(f"Order {order_id} status: {order.status.value}")
                return
        print(f"Order {order_id} not found.")


class Restaurant:
    def __init__(self, restaurant_id: int, name: str, location: Location, menu: List[MenuItem]):
        self.restaurant_id = restaurant_id
        self.name = name
        self.location = location
        self.menu = menu
        self.orders = []

    def accept_order(self, order: Order):
        if order.status == OrderStatus.INITIATED:
            order.update_status(OrderStatus.ACCEPTED)
            self.orders.append(order)
            print(f"Restaurant {self.name} accepted order {order.order_id}")
            return True
        return False

    def reject_order(self, order: Order):
        if order.status == OrderStatus.INITIATED:
            print(f"Restaurant {self.name} rejected order {order.order_id}")
            return True
        return False


class DeliveryAgent:
    def __init__(self, agent_id: int, name: str, location: Location):
        self.agent_id = agent_id
        self.name = name
        self.location = location  # Assume free agents return to initial location
        self.status = "FREE"
        self.current_order = None

    def assign_order(self, order: Order):
        if self.status == "FREE":
            self.status = "BUSY"
            self.current_order = order
            order.delivery_agent = self
            order.update_status(OrderStatus.DEPLOYED)
            print(f"Delivery agent {self.name} assigned to order {order.order_id}")
            return True
        return False

    def complete_delivery(self):
        if self.status == "BUSY" and self.current_order:
            self.current_order.update_status(OrderStatus.DELIVERED)
            self.status = "FREE"
            self.current_order = None
            # Assume agent returns to initial location when free
            print(f"Delivery agent {self.name} completed delivery")
            return True
        return False

class DeliveryPlatform:
    def __init__(self):
        self.customers = {}
        self.restaurants = {}
        self.delivery_agents = {}
        self.orders = {}
        self.order_counter = 0
        self.priority_queue = []  # Max heap for priority orders (using negative priority fee)
        self.normal_queue = []    # Max heap for normal orders

    def add_customer(self, customer: Customer):
        self.customers[customer.customer_id] = customer

    def add_restaurant(self, restaurant: Restaurant):
        self.restaurants[restaurant.restaurant_id] = restaurant

    def add_delivery_agent(self, agent: DeliveryAgent):
        self.delivery_agents[agent.agent_id] = agent

    def create_order(self, customer: Customer, restaurant: Restaurant, items: List[MenuItem], is_priority: bool):
        self.order_counter += 1
        order = Order(self.order_counter, customer, restaurant, items, is_priority)
        self.orders[self.order_counter] = order
        # Add to appropriate queue
        priority_value = -order.delivery_fee if is_priority else -float('inf')
        queue = self.priority_queue if is_priority else self.normal_queue
        heappush(queue, (priority_value, order.order_id))
        return order

    def assign_delivery_agent(self):
        # Processing priority orders first
        while self.priority_queue:
            _, order_id = heappop(self.priority_queue)
            order = self.orders.get(order_id)
            if order and order.status == OrderStatus.ACCEPTED:
                agent = self.find_nearest_agent(order.restaurant.location)
                if agent:
                    agent.assign_order(order)
                    return True
            elif order and order.status != OrderStatus.ACCEPTED:
                # Re-queuing if not yet accepted
                heappush(self.priority_queue, (-order.delivery_fee, order_id))

        # Processing normal orders
        while self.normal_queue:
            _, order_id = heappop(self.normal_queue)
            order = self.orders.get(order_id)
            if order and order.status == OrderStatus.ACCEPTED:
                agent = self.find_nearest_agent(order.restaurant.location)
                if agent:
                    agent.assign_order(order)
                    return True
            elif order and order.status != OrderStatus.ACCEPTED:
                heappush(self.normal_queue, (-float('inf'), order_id))
        return False

    def find_nearest_agent(self, location: Location) -> DeliveryAgent:
        min_distance = float('inf')
        nearest_agent = None
        for agent in self.delivery_agents.values():
            if agent.status == "FREE":
                distance = location.distance_to(agent.location)
                if distance < min_distance:
                    min_distance = distance
                    nearest_agent = agent
        return nearest_agent

    def simulate_step(self):
        self.assign_delivery_agent()


def main():
    platform = DeliveryPlatform()

"""
    #TEST DATA
    customer1 = Customer(1, "Alice", Location(0, 0))
    customer2 = Customer(2, "Bob", Location(10, 10))
    platform.add_customer(customer1)
    platform.add_customer(customer2)

    menu = [MenuItem("Pizza", 10.0), MenuItem("Burger", 5.0)]
    restaurant1 = Restaurant(1, "Food Haven", Location(5, 5), menu)
    restaurant2 = Restaurant(2, "Tasty Bites", Location(8, 8), menu)
    platform.add_restaurant(restaurant1)
    platform.add_restaurant(restaurant2)

    agent1 = DeliveryAgent(1, "Driver1", Location(4, 4))
    agent2 = DeliveryAgent(2, "Driver2", Location(7, 7))
    platform.add_delivery_agent(agent1)
    platform.add_delivery_agent(agent2)

    # Simulate order placement
    order1 = customer1.place_order(platform, restaurant1, [menu[0]], is_priority=True)
    order2 = customer2.place_order(platform, restaurant2, [menu[1]], is_priority=False)

    # Simulate restaurant accepting orders
    restaurant1.accept_order(order1)
    restaurant2.accept_order(order2)

    # Simulate delivery steps
    platform.simulate_step()  # Should assign agent1 to order1 (priority, closer)
    agent1.complete_delivery()  # Complete order1

    platform.simulate_step()  # Should assign agent1 to order2 (now free)
    agent1.complete_delivery()  # Complete order2

    # Check order status
    customer1.check_order_status(order1.order_id)
    customer2.check_order_status(order2.order_id)

"""
#Check if I need to run it as a script or import it as a module
if __name__ == "__main__":
    main()