from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2 import maps
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
import random


class AWollE(BotAI):  # inhereits from BotAI (part of BurnySC2)
    def __init__(self):
        super().__init__()
        self.scout_zerglings_tags = set()
        self.build_order_dict = [
            {"drones": "13", "unit": UnitTypeId.OVERLORD, "requirements": []},
            {"drones": "16", "unit": UnitTypeId.HATCHERY},
            {"drones": "18", "unit": UnitTypeId.EXTRACTOR},
            {"drones": "17", "unit": UnitTypeId.SPAWNINGPOOL},
            {"drones": "19", "unit": UnitTypeId.OVERLORD},
        ]
        self.build_order_done = False
        self.should_rally_reset = 0

    def select_target(self) -> Point2:
        if self.enemy_structures:
            return random.choice(self.enemy_structures).position
        return self.enemy_start_locations[0]

    def ready_and_planned_unit(self, unit: UnitTypeId) -> int:
        return self.units(unit).amount + self.already_pending(unit)

    def ready_and_planned_structure(self, structure: UnitTypeId) -> int:
        return self.structures(structure).ready.amount + self.already_pending(structure)

    def ready_and_planned_upgrade(self, upgrade: UpgradeId) -> int:
        return upgrade in self.state.upgrades or self.already_pending_upgrade(upgrade)

    async def build_order(self):

        supply_used = self.supply_used

        # Build overlord
        if (supply_used == 13 and self.units(UnitTypeId.OVERLORD).amount + self.already_pending(UnitTypeId.OVERLORD) == 1):
            self.train(UnitTypeId.OVERLORD)
            return

        # Hatchery
        elif (supply_used == 16 and self.ready_and_planned_structure(UnitTypeId.HATCHERY) == 1):
            if self.can_afford(UnitTypeId.HATCHERY):
                await self.expand_now()
            return

        # Extractor
        elif (supply_used == 18 and self.ready_and_planned_structure(UnitTypeId.EXTRACTOR) == 0):
            geysers = self.vespene_geyser.closer_than(
                10, self.townhalls.closest_to(self.start_location))
            for geyser in geysers:
                if await self.can_place(UnitTypeId.EXTRACTOR, geyser.position) and self.can_afford(UnitTypeId.EXTRACTOR):
                    await self.build(UnitTypeId.EXTRACTOR, geyser)
                    break
            return

        # Spawning Pool
        elif (supply_used >= 17 and self.ready_and_planned_structure(UnitTypeId.SPAWNINGPOOL) == 0
              # Build first after the extrator has been started/built
              and self.ready_and_planned_structure(UnitTypeId.EXTRACTOR) == 1):
            await self.build_normal_building(UnitTypeId.SPAWNINGPOOL)

        # Overlord
        elif (supply_used >= 19 and self.ready_and_planned_unit(UnitTypeId.OVERLORD) == 2):
            self.train(UnitTypeId.OVERLORD)
            return

        # Queen / Hatchery
        elif supply_used >= 19 and self.ready_and_planned_unit(UnitTypeId.QUEEN) < 2:
            if self.can_afford(UnitTypeId.QUEEN):
                self.train(UnitTypeId.QUEEN)

        # Zergling x6
        elif supply_used >= 24 and self.ready_and_planned_unit(UnitTypeId.ZERGLING) < 3:
            self.train(UnitTypeId.ZERGLING)

         # Overlord
        elif (supply_used >= 30 and self.ready_and_planned_unit(UnitTypeId.OVERLORD) == 3):
            self.train(UnitTypeId.OVERLORD)

        # Queen
        elif (supply_used >= 30 and self.ready_and_planned_unit(UnitTypeId.QUEEN) == 2):
            if self.can_afford(UnitTypeId.QUEEN) and self.townhalls.idle:
                townhall = self.townhalls.idle.furthest_to(self.start_location)
                townhall.train(UnitTypeId.QUEEN)

        # Lair
        elif (supply_used >= 33 and self.ready_and_planned_structure(UnitTypeId.LAIR) == 0 and self.townhalls.closest_to(self.start_location).is_idle):
            hatchery = self.townhalls.closest_to(self.start_location)
            hatchery.build(UnitTypeId.LAIR)

        # Overlord
        elif (supply_used >= 33 and self.ready_and_planned_unit(UnitTypeId.OVERLORD) < 5):
            self.train(UnitTypeId.OVERLORD)

        # Evolution Chamber
        elif (supply_used >= 37 and self.ready_and_planned_structure(UnitTypeId.EVOLUTIONCHAMBER) == 0):
            await self.build_normal_building(UnitTypeId.EVOLUTIONCHAMBER)

        # Roach Warren
        elif (supply_used >= 37 and self.ready_and_planned_structure(UnitTypeId.ROACHWARREN) == 0):
            await self.build_normal_building(UnitTypeId.ROACHWARREN)

        # Overlord
        elif (supply_used >= 44 and self.ready_and_planned_unit(UnitTypeId.OVERLORD) == 5):
            self.train(UnitTypeId.OVERLORD)

        # Zerg Missile Weapons Level 1
        elif (supply_used >= 44 and self.ready_and_planned_upgrade(UpgradeId.ZERGMISSILEWEAPONSLEVEL1) == 0):
            self.research(UpgradeId.ZERGMISSILEWEAPONSLEVEL1)

        # Extractor x2
        elif (supply_used >= 52 and self.ready_and_planned_structure(UnitTypeId.EXTRACTOR) < 3):
            await self.build_extractors(2)

        # Overlord x2
        elif (supply_used >= 50 and self.ready_and_planned_unit(UnitTypeId.OVERLORD) < 7):
            self.train(UnitTypeId.OVERLORD)

        # Glial Reconstitution
        elif (supply_used >= 50 and self.ready_and_planned_upgrade(UpgradeId.GLIALRECONSTITUTION) == 0):
            self.research(UpgradeId.GLIALRECONSTITUTION)

        # Roach x8
        elif (supply_used >= 50 and self.ready_and_planned_unit(UnitTypeId.ROACH) < 8):
            self.train(UnitTypeId.ROACH)

        elif (self.ready_and_planned_unit(UnitTypeId.ROACH) > 1):
            self.build_order_done = True

        else:
            if self.can_afford(UnitTypeId.DRONE):
                self.train(UnitTypeId.DRONE)

    async def build_extractors(self, toBuild: int = 1):
        openVgs = []
        for th in self.townhalls:
            vgs = self.vespene_geyser.closer_than(10, th)
            for vg in vgs:
                if await self.can_place(UnitTypeId.EXTRACTOR, vg.position) and self.can_afford(UnitTypeId.EXTRACTOR):
                    openVgs.append(vg)

        for vg in openVgs:
            await self.build(UnitTypeId.EXTRACTOR, vg)
            toBuild = toBuild - 1
            if toBuild == 0:
                break

    async def build_normal_building(self, building_id: UnitTypeId):
        map_center = self.game_info.map_center
        position_towards_map_center = self.start_location.towards(
            map_center, distance=5)
        await self.build(building_id, near=position_towards_map_center, placement_step=1)


    def set_rally_point(self, reset:bool = False):

        if (reset): 
            self.hatcheryRallyPointsSet = {}

        if hasattr(self, "hatcheryRallyPointsSet"):
            for hatch in self.townhalls:
                if hatch.tag not in self.hatcheryRallyPointsSet:
                    # abilities = await self.get_available_abilities(hatch)
                    # if RALLY_HATCHERY_WORKERS in abilities:
                    # rally workers to nearest mineral field
                    map_center = self.game_info.map_center
                    rallyPoint = self.townhalls.furthest_to(self.start_location).position.towards(map_center, distance=15)
                    suc = hatch(AbilityId.RALLY_UNITS, rallyPoint)
                    print(suc)
                    if suc:
                        self.hatcheryRallyPointsSet[hatch.tag] = rallyPoint
        else:
            self.hatcheryRallyPointsSet = {}

    # on_step is a method that is called every step of the game.
    async def on_step(self, iteration: int):
        if iteration == 0:
            await self.chat_send("(glhf)")

        print(f"{iteration}, tot_workers: {self.ready_and_planned_unit(UnitTypeId.DRONE)}, n_workers: {self.workers.amount},",
              f"minerals: {self.minerals}, gas: {self.vespene},",
              f"overlords: {self.units(UnitTypeId.OVERLORD).amount}, hatcheries: {self.structures(UnitTypeId.HATCHERY).amount}",
              f"zerglings: {self.units(UnitTypeId.ZERGLING).amount}, larva: {self.units(UnitTypeId.LARVA).amount}",
              f"supply: {self.supply_used}/{self.supply_cap}")

        # begin logic:
        await self.distribute_workers()  # put idle workers back to work

        # move units to expansion towards center
        if (self.townhalls.amount != self.should_rally_reset):
            self.set_rally_point(True)
        self.should_rally_reset = self.townhalls.amount
        

        if self.townhalls:
            if (not self.build_order_done):
                await self.build_order()
            else:
                # max overlords and roaches
                if self.supply_left < 8 and not self.already_pending(UnitTypeId.OVERLORD):
                    self.train(UnitTypeId.OVERLORD)

                if (self.ready_and_planned_structure(UnitTypeId.ROACHWARREN)):
                    self.train(UnitTypeId.ROACH)

                for building in [UnitTypeId.SPAWNINGPOOL, UnitTypeId.EVOLUTIONCHAMBER, UnitTypeId.ROACHWARREN]:
                    if self.ready_and_planned_structure(building) == 0:
                        await self.build_normal_building(building)

                if (self.units(UnitTypeId.ROACH).amount > 25):
                    for roach in self.units(UnitTypeId.ROACH):
                        if roach.is_idle:
                            if roach.distance_to(self.enemy_start_locations[0]) > 30:
                                roach.attack(self.enemy_start_locations[0])
                            elif self.enemy_units.amount:
                                roach.attack(self.enemy_units.random.position)
                            elif self.enemy_structures.amount:
                                roach.attack(self.enemy_structures.random.position)
                            else:
                                roach.move(random.choice(self.expansion_locations_list))
                        
                    
            if False:
                if self.can_afford(UnitTypeId.DRONE) and self.supply_workers < self.townhalls.amount * 18:
                    for loop_larva in self.larva:
                        if self.can_afford(UnitTypeId.DRONE) and self.supply_workers < self.townhalls.amount * 18:
                            loop_larva.train(UnitTypeId.DRONE)
                        else:
                            break  # Can't afford drones anymore

                if self.can_afford(UnitTypeId.HATCHERY) and (self.workers.amount > (14 * self.townhalls.amount)) and self.townhalls.amount <= 3 and not self.already_pending(UnitTypeId.HATCHERY):
                    await self.expand_now()

                if self.can_afford(UnitTypeId.OVERLORD) and self.supply_left < (12 * self.townhalls.amount) and self.already_pending(UnitTypeId.OVERLORD) == 0 and self.supply_cap < 200:
                    self.train(UnitTypeId.OVERLORD)

                if self.can_afford(UnitTypeId.SPAWNINGPOOL) and self.already_pending(UnitTypeId.SPAWNINGPOOL) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.SPAWNINGPOOL and structure.is_ready).amount == 0:
                    map_center = self.game_info.map_center
                    position_towards_map_center = self.start_location.towards(
                        map_center, distance=5)
                    await self.build(UnitTypeId.SPAWNINGPOOL, near=position_towards_map_center, placement_step=1)

                if self.can_afford(UnitTypeId.QUEEN) and self.units(UnitTypeId.QUEEN).amount < self.structures(UnitTypeId.HATCHERY).amount and self.already_pending(UnitTypeId.QUEEN) == 0 and self.structures(UnitTypeId.SPAWNINGPOOL).filter(lambda structure: structure.is_ready).amount != 0:

                    if self.units(UnitTypeId.QUEEN):
                        for townhall in self.townhalls:
                            if self.units(UnitTypeId.QUEEN).closest_to(townhall).distance_to(townhall) > 15:
                                townhall.train(UnitTypeId.QUEEN)
                    else:
                        self.townhalls.random.train(UnitTypeId.QUEEN)

                if self.can_afford(UnitTypeId.ZERGLING) and self.structures(UnitTypeId.SPAWNINGPOOL).filter(lambda structure: structure.is_ready).amount != 0:
                    self.train(UnitTypeId.ZERGLING)

                # build refineries (on nearby vespene) when at least one barracks is in construction
                if self.can_afford(UnitTypeId.EXTRACTOR) and self.structures(UnitTypeId.SPAWNINGPOOL).amount > 0 and self.already_pending(UnitTypeId.EXTRACTOR) < 1:
                    for th in self.townhalls:
                        vgs = self.vespene_geyser.closer_than(10, th)
                        for vg in vgs:
                            if await self.can_place(UnitTypeId.EXTRACTOR, vg.position) and self.can_afford(UnitTypeId.EXTRACTOR):
                                ws = self.workers.gathering
                                if ws.exists:  # same condition as above
                                    w = ws.closest_to(vg)
                                    w.build(UnitTypeId.EXTRACTOR, vg)

        else:
            if False:
                if self.can_afford(UnitTypeId.HATCHERY) and not self.already_pending(UnitTypeId.HATCHERY):
                    await self.expand_now()

        for queen in self.units(UnitTypeId.QUEEN).idle.filter(lambda unit: unit.energy >= 25):
            if (self.townhalls.closest_to(queen).distance_to(queen) < 15):
                if await self.can_cast(queen, AbilityId.EFFECT_INJECTLARVA, self.townhalls.closest_to(queen)):
                    queen(AbilityId.EFFECT_INJECTLARVA,
                          self.townhalls.closest_to(queen))

        if self.units(UnitTypeId.ZERGLING).amount > 20:
            for zergling in self.units(UnitTypeId.ZERGLING):
                zergling.attack(self.enemy_start_locations[0])

        elif self.units(UnitTypeId.ZERGLING).amount > 0:
            if self.units.tags_in(self.scout_zerglings_tags).amount <= 2:
                for zergling in self.units(UnitTypeId.ZERGLING).tags_not_in(self.scout_zerglings_tags):
                    self.scout_zerglings_tags.add(zergling.tag)

            if self.units.tags_in(self.scout_zerglings_tags).amount > 0:
                for zergling in self.units.tags_in(self.scout_zerglings_tags):
                    if self.enemy_units and self.enemy_units.closest_distance_to(zergling) < 15:
                        zergling.move(self.start_location)
                    elif (self.enemy_units and self.enemy_units.closest_distance_to(zergling) < 30) or (zergling.is_idle):
                        zergling.move(random.choice(
                            self.expansion_locations_list))

        if self.structures(UnitTypeId.SPAWNINGPOOL).amount != 0 and self.can_afford(UpgradeId.ZERGLINGMOVEMENTSPEED):
            self.research(UpgradeId.ZERGLINGMOVEMENTSPEED)


def main():
    run_game(  # run_game is a function that runs the game.
        maps.get("2000AtmospheresAIE"),  # the map we are playing on
        [Bot(Race.Zerg, AWollE()),  # runs our coded bot, protoss race, and we pass our bot object
         Computer(Race.Random, Difficulty.Hard)],  # runs a pre-made computer agent, zerg race, with a hard difficulty.
        # When set to True, the agent is limited in how long each step can take to process.
        realtime=False,
    )


if __name__ == "__main__":
    main()
