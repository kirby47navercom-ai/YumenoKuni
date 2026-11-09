"""Production walking links for existing dedicated sets, not recovered V3 geography.

The active authored hub still restricts which links are offered at runtime.
These add no chapter unlock, evidence, or story route.
"""
from copy import deepcopy

LINKS = [
    ('plaza', 'souvenir_forecourt', [10, 1.2, 4], [0, 1.2, 7.2]),
    ('souvenir_forecourt', 'souvenir_shop', [0, 1.2, 4.05], [0, 1.2, 3.5]),
    ('plaza', 'can_toss_booth', [11, 1.2, 8], [0, 1.2, 5.7]),
    ('hotel_lobby', 'hotel_indoor_garden', [-6.7, 1.2, -3], [0, 1.2, 5.5]),
    ('hotel_indoor_garden', 'garden_rest_area', [3.6, 1.2, 2.1], [3.6, 1.2, 2.1]),
    ('hotel_corridor', 'hotel_rest_lounge', [1.88, 1.2, 3], [0, 1.2, 5.5]),
    ('hotel_corridor', 'hotel_washroom', [1.88, 1.2, -4], [0, 1.2, 4]),
]


def apply(world):
    for a, b, pa, pb in LINKS:
        assert a in world['instances'] and b in world['instances'], (a, b)
        row = dict(id='fte_path:' + a + ':' + b, a=a, b=b, kind='scene_portal',
                   a_p=pa, b_p=pb, productionLayout=True, reaGeometryRecovered=False)
        prior = next((e for e in world['connections'] if e['id'] == row['id']), None)
        if prior is not None:
            assert prior == row, 'Do not overwrite a different authored connection'
        else:
            world['connections'].append(deepcopy(row))
    return world
