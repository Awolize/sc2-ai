import unittest
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer 
from sc2 import maps
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
import random

class IncrediBot(BotAI): # inhereits from BotAI (part of BurnySC2)
    async def on_step(self, iteration: int): # on_step is a method that is called every step of the game.
        print(f"{iteration}, n_workers: {self.workers.amount}, n_idle_workers: {self.workers.idle.amount},", \
            f"minerals: {self.minerals}, gas: {self.vespene},", \
            f"overlords: {self.units(UnitTypeId.OVERLORD).amount}, hatcheries: {self.structures(UnitTypeId.HATCHERY).amount}", \
            f"zerglings: {self.units(UnitTypeId.ZERGLING).amount}, larva: {self.units(UnitTypeId.LARVA).amount}", \
            f"supply: {self.supply_used}/{self.supply_cap}")
        
        
        # begin logic:
        await self.distribute_workers() # put idle workers back to work



        if self.townhalls:
            if self.can_afford(UnitTypeId.DRONE) and self.supply_workers < self.townhalls.amount * 18:  
                for townhall in self.townhalls:
                    if townhall.is_idle:
                        townhall.train(UnitTypeId.DRONE)

            if self.can_afford(UnitTypeId.HATCHERY) and (self.workers.amount > (14*self.structures(UnitTypeId.HATCHERY).amount)) and self.already_pending(UnitTypeId.HATCHERY) == 0:
                await self.expand_now()
            
            if self.can_afford(UnitTypeId.OVERLORD) and self.supply_left < (10 * self.townhalls.amount) and self.already_pending(UnitTypeId.OVERLORD) == 0 and self.supply_cap < 200:
                self.train(UnitTypeId.OVERLORD, 1)

            if self.can_afford(UnitTypeId.SPAWNINGPOOL) and self.already_pending(UnitTypeId.SPAWNINGPOOL) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.SPAWNINGPOOL and structure.is_ready).amount == 0:
                map_center = self.game_info.map_center
                position_towards_map_center = self.start_location.towards(map_center, distance=5)
                await self.build(UnitTypeId.SPAWNINGPOOL, near=position_towards_map_center, placement_step=1)

            if self.can_afford(UnitTypeId.QUEEN) and self.units(UnitTypeId.QUEEN).amount < self.structures(UnitTypeId.HATCHERY).amount and self.already_pending(UnitTypeId.QUEEN) == 0 and self.structures(UnitTypeId.SPAWNINGPOOL).filter(lambda structure: structure.is_ready).amount != 0:
                townhall_candidates = self.townhalls
                for townhall in self.townhalls:
                    if townhall in townhall_candidates:
                        for queen in self.units(UnitTypeId.QUEEN):
                            if townhall.distance_to(queen) < 15:
                                townhall_candidates.remove(townhall)
                                break

                if townhall_candidates:
                    for townhall_candidate in townhall_candidates:
                        townhall_candidate.train(UnitTypeId.QUEEN)

            if self.can_afford(UnitTypeId.ZERGLING) and self.structures(UnitTypeId.SPAWNINGPOOL).filter(lambda structure: structure.is_ready).amount != 0:
                self.train(UnitTypeId.ZERGLING)

        else:
            if self.can_afford(UnitTypeId.HATCHERY): 
                await self.expand_now()


        for queen in self.units.filter(lambda unit: unit.type_id == UnitTypeId.QUEEN and unit.energy >= 25):
            queen.in_ability_cast_range(AbilityId.EFFECT_INJECTLARVA, self.townhalls.closest_to(queen))

        if self.units(UnitTypeId.ZERGLING).amount > 20:
            for zergling in self.units(UnitTypeId.ZERGLING):
                zergling.attack(self.enemy_start_locations[0])


run_game(  # run_game is a function that runs the game.
    maps.get("2000AtmospheresAIE"), # the map we are playing on
    [Bot(Race.Zerg, IncrediBot()), # runs our coded bot, protoss race, and we pass our bot object 
     Computer(Race.Random, Difficulty.Hard)], # runs a pre-made computer agent, zerg race, with a hard difficulty.
    realtime=False, # When set to True, the agent is limited in how long each step can take to process.
)