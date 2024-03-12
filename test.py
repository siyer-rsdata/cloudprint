from libs.constants import Environment, get_constant
from libs.auth import Auth

# Singleton instance of Environment class, loads constants in the OS environment.
env = Environment()

print("CPUTIL_LOCATION: ", get_constant("CPUTIL_LOCATION"))

auth = Auth()

print("Test result: ", auth.is_active("fake_restaurant_for_testing"))

