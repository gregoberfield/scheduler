"""
Group name generator for creating fun, unique group names.
Combines random adjectives with animal nouns (e.g., "Hairy Porpoises").
"""
import random
from app import db

# Curated list of adjectives
ADJECTIVES = [
    'Agile', 'Bold', 'Brave', 'Clever', 'Daring',
    'Eager', 'Fierce', 'Gentle', 'Happy', 'Jolly',
    'Keen', 'Lively', 'Mighty', 'Noble', 'Quick',
    'Rapid', 'Silent', 'Swift', 'Valiant', 'Wise',
    'Zealous', 'Ancient', 'Blazing', 'Crafty', 'Dazzling',
    'Epic', 'Frosty', 'Golden', 'Hairy', 'Iron',
    'Jumpy', 'Kingly', 'Lucky', 'Mystic', 'Nimble',
    'Omega', 'Primal', 'Quirky', 'Raging', 'Savage',
    'Toxic', 'Ultra', 'Vicious', 'Wicked', 'Xenial',
    'Young', 'Zesty', 'Arcane', 'Blessed', 'Cursed',
    'Divine', 'Elusive', 'Flaming', 'Glorious', 'Howling',
    'Icy', 'Jagged', 'Knotted', 'Luminous', 'Molten',
]

# Curated list of animal nouns (plural)
ANIMALS = [
    'Badgers', 'Bears', 'Cats', 'Dogs', 'Eagles',
    'Falcons', 'Geese', 'Hawks', 'Ibises', 'Jaguars',
    'Kestrels', 'Lions', 'Moose', 'Newts', 'Owls',
    'Porpoises', 'Quails', 'Ravens', 'Serpents', 'Tigers',
    'Urchins', 'Vultures', 'Wolves', 'Yaks', 'Zebras',
    'Ants', 'Beetles', 'Crows', 'Drakes', 'Elk',
    'Foxes', 'Gazelles', 'Hounds', 'Impalas', 'Jackals',
    'Koalas', 'Lemurs', 'Mantises', 'Narwhals', 'Otters',
    'Pandas', 'Pythons', 'Raccoons', 'Sharks', 'Turtles',
    'Unicorns', 'Vipers', 'Weasels', 'Wyrms', 'Yetis',
    'Zombies', 'Alpacas', 'Boars', 'Chimeras', 'Dragonflies',
    'Elephants', 'Frogs', 'Gorillas', 'Hydras', 'Iguanas',
]


def generate_unique_group_name(max_attempts=10):
    """
    Generate a unique group name by combining random adjective + animal.
    Retries until a unique name is found or max_attempts reached.
    
    Args:
        max_attempts: Maximum number of attempts to find unique name
        
    Returns:
        str: Unique group name (e.g., "Hairy Porpoises")
        
    Raises:
        ValueError: If unable to generate unique name after max_attempts
    """
    # Import here to avoid circular dependency
    from app.models.group import Group
    
    for attempt in range(max_attempts):
        adjective = random.choice(ADJECTIVES)
        animal = random.choice(ANIMALS)
        name = f"{adjective} {animal}"
        
        # Check if name already exists
        existing = Group.query.filter_by(name=name).first()
        if not existing:
            return name
    
    # If we get here, we failed to find a unique name
    raise ValueError(
        f"Failed to generate unique group name after {max_attempts} attempts. "
        f"Consider expanding the word lists or clearing old groups."
    )


def get_random_group_name():
    """
    Get a random group name without checking uniqueness.
    Useful for previews or testing.
    
    Returns:
        str: Random group name
    """
    adjective = random.choice(ADJECTIVES)
    animal = random.choice(ANIMALS)
    return f"{adjective} {animal}"
