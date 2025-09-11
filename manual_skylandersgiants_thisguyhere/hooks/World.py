# Object classes from AP core, to represent an entire MultiWorld and this individual World that's part of it
from worlds.AutoWorld import World
from BaseClasses import MultiWorld, CollectionState, Item, ItemClassification, Entrance

# Object classes from Manual -- extending AP core -- representing items and locations that are used in generation
from ..Items import ManualItem
from ..Locations import ManualLocation

# Raw JSON data from the Manual apworld, respectively:
#          data/game.json, data/items.json, data/locations.json, data/regions.json
#
from ..Data import game_table, item_table, location_table, region_table

# These helper methods allow you to determine if an option has been set, or what its value is, for any player in the multiworld
from ..Helpers import is_option_enabled, get_option_value, format_state_prog_items_key, ProgItemsCat, is_location_name_enabled, is_item_name_enabled

# calling logging.info("message") anywhere below in this file will output the message to both console and log file
import logging

########################################################################################
## Order of method calls when the world generates:
##    1. create_regions - Creates regions and locations
##    2. create_items - Creates the item pool
##    3. set_rules - Creates rules for accessing regions and locations
##    4. generate_basic - Runs any post item pool options, like place item/category
##    5. pre_fill - Creates the victory location
##
## The create_item method is used by plando and start_inventory settings to create an item from an item name.
## The fill_slot_data method will be used to send data to the Manual client for later use, like deathlink.
########################################################################################



# Use this function to change the valid filler items to be created to replace item links or starting items.
# Default value is the `filler_item_name` from game.json
def hook_get_filler_item_name(world: World, multiworld: MultiWorld, player: int) -> str | bool:
    return False

# Called before regions and locations are created. Not clear why you'd want this, but it's here. Victory location is included, but Victory event is not placed yet.
def before_create_regions(world: World, multiworld: MultiWorld, player: int):
    pass

# Called after regions and locations are created, in case you want to see or modify that information. Victory location is included.
def after_create_regions(world: World, multiworld: MultiWorld, player: int):
    # Use this hook to remove locations from the world
    locationNamesToRemove: list[str] = [] # List of location names

    # Add your code here to calculate which locations to remove
        

    for region in multiworld.regions:
        if region.player == player:
            for location in list(region.locations):
                if location.name in locationNamesToRemove:
                    region.locations.remove(location)
    if hasattr(multiworld, "clear_location_cache"):
        multiworld.clear_location_cache()

    # in non-linear mode, we need to make the hub the new starting region and connect it to all chapters
    # this is doing better than the other methods, but the output shows that I can immediately achieve victory
    if get_option_value(multiworld, player, "linear_mode"):
        # get rid of the chapter exits in Hub and the hub entrances in the chapters
       
        # in linear mode, start by removing the connection between "Manual" and "Hub"
        hub = multiworld.get_region("Hub", player)
        manual = multiworld.get_region("Manual", player)
        manual.exits = [exit for exit in manual.exits if "Hub" not in exit.name]
        hub.entrances = [entrance for entrance in hub.entrances if "Manual" not in entrance.name.split("To")[0]]
        
        # remove the hub link from final boss
        hub.exits = [exit for exit in hub.exits if "Final Boss" not in exit.name]
        boss = multiworld.get_region("Final Boss", player)
        boss.entrances = [entrance for entrance in boss.entrances if "Hub" not in entrance.name]

        # then the connections between "Hub" and the numbered chapters
        hub.exits = [exit for exit in hub.exits if "Chapter" not in exit.name.split("To", 2)[1]]
        for region in multiworld.regions:
            if region.player == player and "Chapter" in region.name:
                region.entrances = [enter for enter in region.entrances if "Hub" not in enter.name.split("To")[0]]
    else:
        # in nonlinear mode, start by removing the connection between "Manual" and "Chapter 1"
        hub = multiworld.get_region("Hub", player)
        chap_1 = multiworld.get_region("Chapter 1", player)
        manual = multiworld.get_region("Manual", player)
        manual.exits = [exit for exit in manual.exits if "Chapter 1" not in exit.name.split("To", 2)[1]]
        chap_1.entrances = [entrance for entrance in chap_1.entrances if "Manual" not in entrance.name.split("To")[0]]

        # remove the chapter 16 link from final boss
        c_16 = multiworld.get_region("Chapter 16", player)
        c_16.exits = [exit for exit in c_16.exits if "Final Boss" not in exit.name]
        boss = multiworld.get_region("Final Boss", player)
        boss.entrances = [entrance for entrance in boss.entrances if "Chapter 16" not in entrance.name]

        # then the connections between each set of numbered chapters
        hub.entrances = [enter for enter in hub.entrances if "Chapter" not in enter.name.split("To", 2)[0]]
        for region in multiworld.regions:
            if region.player == player and "Chapter" in region.name:
                region.exits = [exit for exit in region.entrances if "Chapter" not in exit.name.split("To", 2)[1] and "Hub" not in exit.name.split("To", 2)[1]]
                region.entrances = [enter for enter in region.entrances if "Chapter" not in enter.name.split("To", 2)[0]]
        '''# new idea: don't remove the entrances and exits, but change their links
        # i.e. get Manual's exit and change the 
        manual = multiworld.get_region("Manual", player)
        hub = multiworld.get_region("Hub", player)

        manual.exits.clear()    # this exit needs to go between Hub and Chapter 1 instead
        #manual.exits[0].connected_region = hub
        #manual.exits[0].name = "ManualToHub"
        hub.entrances[0].name = "ManualToHub"   # for the sake of simplicity, we'll remap the entrance to a region to the "previous" region
        manual.exits.append(hub.entrances[0])
        # we don't need to remove Hub's exits because the ones it has are still necessary

        for region in multiworld.regions:
            if region.player == player and "Chapter" in region.name:
                # rename each entrance and add it to the exits of Hub, then remove this region's exits (chapters shouldn't have any). also rename it
                current_entrance = region.entrances[0]
                hub.exits.append(current_entrance)
                current_entrance.name = f"HubTo{region.name}"
                region.exits.clear()

                #chapters.append(region.name)
                #new_exit = hub.add_exits([region.name])
                #add_rule(world.get_entrance(new_exit[0].name), fullRegionCheck) # I need to add the requirements for each ofthese regions'''


        '''from worlds.generic.Rules import add_rule
        
        manual = multiworld.get_region("Manual", player)
        hub = multiworld.get_region("Hub", player)
        chapters = []

        hub.entrances.clear()
        manual.set_exits([])
        manual.add_exits([hub.name])

        for region in multiworld.regions:
            if region.player == player and "Chapter" in region.name:
                region.set_exits([])            # the chapters shouldn't have exits in this mode
                region.entrances.clear()
                chapters.append(region.name)
                #new_exit = hub.add_exits([region.name])
                #add_rule(world.get_entrance(new_exit[0].name), fullRegionCheck) # I need to add the requirements for each ofthese regions
        hub.add_exits(chapters)'''



# This hook allows you to access the item names & counts before the items are created. Use this to increase/decrease the amount of a specific item in the pool
# Valid item_config key/values:
# {"Item Name": 5} <- This will create qty 5 items using all the default settings
# {"Item Name": {"useful": 7}} <- This will create qty 7 items and force them to be classified as useful
# {"Item Name": {"progression": 2, "useful": 1}} <- This will create 3 items, with 2 classified as progression and 1 as useful
# {"Item Name": {0b0110: 5}} <- If you know the special flag for the item classes, you can also define non-standard options. This setup
#       will create 5 items that are the "useful trap" class
# {"Item Name": {ItemClassification.useful: 5}} <- You can also use the classification directly
def before_create_items_all(item_config: dict[str, int|dict], world: World, multiworld: MultiWorld, player: int) -> dict[str, int|dict]:
    return item_config

# The item pool before starting items are processed, in case you want to see the raw item pool at that stage
def before_create_items_starting(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:

    # Use this hook to remove items from the item pool
    itemNamesToRemove = [] # List of item names
    locationNamesToRemove = [] # List of location names

    # Add your code here to calculate which items to remove.
    #
    # Because multiple copies of an item can exist, you need to add an item name
    # to the list multiple times if you want to remove multiple copies of it.
    
    # if a character is not in the list and whitelist is enabled OR a character is in the list and whitelist is disabled, remove that item
    names_to_remove = get_option_value(multiworld, player, "characters_to_exclude")
    use_character_whitelist = get_option_value(multiworld, player, "whitelist_characters")
    challenges_enabled = get_option_value(multiworld, player, "challenges_as_locations")

    if use_character_whitelist and len(names_to_remove) < 8:
        raise Exception("Whitelist was enabled, but does not contain enough skylanders. For optimal results, please ensure that the whitelist " + 
                        "contains at least 8 skylanders, at least one from each element, and at least one giant.")

    # need to first check if the item is in item_pool
    for item in item_table:
        #table_item = next(i for i in item_table if i["name"] == item.name)
        if "category" not in item or "Skylander" not in item.get("category") or not is_item_name_enabled(multiworld,player,item.get("name")):
            continue
        item_name = item.get("name")
        character_in_list = False
        #for char_name in names_to_remove:
        #    if item_name.casefold() == char_name.casefold():
        #        character_in_list = True
        #        break
        if item_name in names_to_remove:
            character_in_list = True

        if (use_character_whitelist ^ character_in_list):
            itemNamesToRemove.append(item_name)
            # get rid of heroic challenges for removed characters
            if (challenges_enabled):
                locationNamesToRemove.append(f"Heroic Challenge - {item_name}")

    if challenges_enabled:
        for region in multiworld.regions:
            if region.player == player:
                for location in list(region.locations):
                    if location.name in locationNamesToRemove:
                        region.locations.remove(location)
                        print(f"Successfully removed Heroic Challenge - {itemName}")   # debug
        if hasattr(multiworld, "clear_location_cache"):
            multiworld.clear_location_cache()

    for itemName in itemNamesToRemove:
        item = next(i for i in item_pool if i.name == itemName)
        item_pool.remove(item)
        print("Successfully removed " + itemName)   # debug

    return item_pool

# The item pool after starting items are processed but before filler is added, in case you want to see the raw item pool at that stage
def before_create_items_filler(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    # Use this hook to remove items from the item pool
    itemNamesToRemove: list[str] = [] # List of item names

    # Add your code here to calculate which items to remove.
    #
    # Because multiple copies of an item can exist, you need to add an item name
    # to the list multiple times if you want to remove multiple copies of it.


    # if playing nonlinear mode, we need to place Map of Arkus Fragments in the chapter locations and remove any extras
    if not get_option_value(multiworld, player, "linear_mode"):
        extra_map_frags = (4 - get_option_value(multiworld, player, "include_empire") - 
                           get_option_value(multiworld, player, "include_ship") - 
                           get_option_value(multiworld, player, "include_crypt") - 
                           get_option_value(multiworld, player, "include_peak"))
        
        for i in range(extra_map_frags):
            itemNamesToRemove.append("Map of Arkus Fragment")

        for location in location_table:
            if "Level Completion" in location["category"] and is_location_name_enabled(multiworld,player,location["name"]): 
                level = multiworld.get_location(location["name"], player)
                item_to_place = next(i for i in item_pool if i.name == "Map of Arkus Fragment")
                level.place_locked_item(item_to_place)
                item_pool.remove(item_to_place)
        


    for itemName in itemNamesToRemove:
        item = next(i for i in item_pool if i.name == itemName)
        item_pool.remove(item)


    # since the traps are weight-based, trap and filler generation needs to be overridden here
    
    extras = len(multiworld.get_unfilled_locations(player=player)) - len(item_pool)

    if extras > 0:
        traps = [item["name"] for item in item_table if item.get("trap")]
        filler = [item["name"] for item in item_table if item.get("filler")]
        #filler.append(world.get_filler_item_name())    # not really necessary anymore
        trap_percent = get_option_value(multiworld, player, "filler_traps")
        if not traps:
            trap_percent = 0

        trap_count = extras * trap_percent // 100
        filler_count = extras - trap_count

        weights = []
            
        for trap in traps:
            option_name = trap.casefold().replace(" ","_") + "_weight"
            weights.append(get_option_value(multiworld,player,option_name))

        if sum(weights) == 0:
            logging.warning(f"{world.player_name} thought setting all trap weights to 0 would be funny. They won't be laughing for long.")
            weights[-1] = 1

        for _ in range(0, trap_count):
            extra_item = world.create_item(world.random.choices(traps,weights=weights)[0])
            item_pool.append(extra_item)

        for _ in range(0, filler_count):
            extra_item = world.create_item(world.random.choice(filler))
            item_pool.append(extra_item)

    return item_pool

    # Some other useful hook options:

    ## Place an item at a specific location
    # location = next(l for l in multiworld.get_unfilled_locations(player=player) if l.name == "Location Name")
    # item_to_place = next(i for i in item_pool if i.name == "Item Name")
    # location.place_locked_item(item_to_place)
    # item_pool.remove(item_to_place)

# The complete item pool prior to being set for generation is provided here, in case you want to make changes to it
def after_create_items(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    return item_pool

# Called before rules for accessing regions and locations are created. Not clear why you'd want this, but it's here.
def before_set_rules(world: World, multiworld: MultiWorld, player: int):
    pass

# Called after rules for accessing regions and locations are created, in case you want to see or modify that information.
def after_set_rules(world: World, multiworld: MultiWorld, player: int):
    # Use this hook to modify the access rules for a given location

    def Example_Rule(state: CollectionState) -> bool:
        # Calculated rules take a CollectionState object and return a boolean
        # True if the player can access the location
        # CollectionState is defined in BaseClasses
        return True
    
    # test #1: try the original code here and see what happens
    # test #2: if 1 doesn't work, add both sets of connections to the regions file and remove the unnecessary ones here. may need to omit Chapter 2ToHub
    
    '''this doesn't work'''

    # in non-linear mode, we need to make the hub the new starting region and connect it to all chapters
    if get_option_value(multiworld, player, "linear_mode"):
        
        ''' # new idea: don't remove the entrances and exits, but change their links
        # i.e. get Manual's exit and change the 
        manual = multiworld.get_region("Manual", player)
        hub = multiworld.get_region("Hub", player)

        manual.exits.clear()    # this exit needs to go between Hub and Chapter 1 instead
        hub.entrances.clear()
        manual.add_exits(["Hub"])
        #manual.exits[0].connected_region = hub
        #manual.exits[0].name = "ManualToHub"
        #hub.entrances[0].name = "ManualToHub"   # for the sake of simplicity, we'll remap the entrance to a region to the "previous" region
        #manual.exits.append(hub.entrances[0])
        # we don't need to remove Hub's exits because the ones it has are still necessary

        for region in multiworld.regions:
            if region.player == player and "Chapter" in region.name:
                # rename each entrance and add it to the exits of Hub, then remove this region's exits (chapters shouldn't have any). also rename it
                current_entrance = region.entrances[0]
                hub.exits.append(current_entrance)
                current_entrance.name = f"HubTo{region.name}"
                region.exits.clear()

                #chapters.append(region.name)
                #new_exit = hub.add_exits([region.name])
                #add_rule(world.get_entrance(new_exit[0].name), fullRegionCheck) # I need to add the requirements for each ofthese regions


        #hub = multiworld.get_region("Hub", player)
        for exit in hub.exits:
            if exit.name == "HubToFinalBoss":
                exit.access_rule = lambda state: state.has(item="Map of Arkus Fragment", player=player, count=get_option_value(multiworld, player, "chapters_to_beat"))
            elif "Chapter" in exit.name:
                # split HubTo... to get the chapter, find that region in the region table, grab the level name from the requires string, profit
                chapter_name = exit.name.split("To", 2)[1]
                level_name = region_table[chapter_name]["requires"].split("|")[3]
                exit.access_rule = lambda state: state.has(item=level_name, player=player, count=1)'''



    ## Common functions:
    # location = world.get_location(location_name, player)
    # location.access_rule = Example_Rule

    ## Combine rules:
    # old_rule = location.access_rule
    # location.access_rule = lambda state: old_rule(state) and Example_Rule(state)
    # OR
    # location.access_rule = lambda state: old_rule(state) or Example_Rule(state)

# The item name to create is provided before the item is created, in case you want to make changes to it
def before_create_item(item_name: str, world: World, multiworld: MultiWorld, player: int) -> str:
    return item_name

# The item that was created is provided after creation, in case you want to modify the item
def after_create_item(item: ManualItem, world: World, multiworld: MultiWorld, player: int) -> ManualItem:
    return item

# This method is run towards the end of pre-generation, before the place_item options have been handled and before AP generation occurs
def before_generate_basic(world: World, multiworld: MultiWorld, player: int):
    pass

# This method is run at the very end of pre-generation, once the place_item options have been handled and before AP generation occurs
def after_generate_basic(world: World, multiworld: MultiWorld, player: int):
    pass

# This method is run every time an item is added to the state, can be used to modify the value of an item.
# IMPORTANT! Any changes made in this hook must be cancelled/undone in after_remove_item
def after_collect_item(world: World, state: CollectionState, Changed: bool, item: Item):
    # the following let you add to the Potato Item Value count
    # if item.name == "Cooked Potato":
    #     state.prog_items[item.player][format_state_prog_items_key(ProgItemsCat.VALUE, "Potato")] += 1
    pass

# This method is run every time an item is removed from the state, can be used to modify the value of an item.
# IMPORTANT! Any changes made in this hook must be first done in after_collect_item
def after_remove_item(world: World, state: CollectionState, Changed: bool, item: Item):
    # the following let you undo the addition to the Potato Item Value count
    # if item.name == "Cooked Potato":
    #     state.prog_items[item.player][format_state_prog_items_key(ProgItemsCat.VALUE, "Potato")] -= 1
    pass


# This is called before slot data is set and provides an empty dict ({}), in case you want to modify it before Manual does
def before_fill_slot_data(slot_data: dict, world: World, multiworld: MultiWorld, player: int) -> dict:
    return slot_data

# This is called after slot data is set and provides the slot data at the time, in case you want to check and modify it after Manual is done with it
def after_fill_slot_data(slot_data: dict, world: World, multiworld: MultiWorld, player: int) -> dict:
    return slot_data

# This is called right at the end, in case you want to write stuff to the spoiler log
def before_write_spoiler(world: World, multiworld: MultiWorld, spoiler_handle) -> None:
    pass

# This is called when you want to add information to the hint text
def before_extend_hint_information(hint_data: dict[int, dict[int, str]], world: World, multiworld: MultiWorld, player: int) -> None:
    
    ### Example way to use this hook: 
    # if player not in hint_data:
    #     hint_data.update({player: {}})
    # for location in multiworld.get_locations(player):
    #     if not location.address:
    #         continue
    #
    #     use this section to calculate the hint string
    #
    #     hint_data[player][location.address] = hint_string
    
    pass

def after_extend_hint_information(hint_data: dict[int, dict[int, str]], world: World, multiworld: MultiWorld, player: int) -> None:
    pass
