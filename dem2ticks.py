# for demo json structure, see:https://awpy.readthedocs.io/en/latest/parser_output.html
import json
import sys
from awpy.parser import DemoParser


def get_all_players(dem_data,round_num):
    ":return all playerid"
    try:
        ct =[each["steamID"] for each in dem_data["gameRounds"][round_num]["ctSide"]["players"]]
        t = [each["steamID"] for each in dem_data["gameRounds"][round_num]["tSide"]["players"]]
    except:
        pass
        # # 遇到错误就换下一局
        # print("ERROR"," ROUND", round_num)
        # print(dem_data["gameRounds"][round_num]["tSide"]["players"])
        # ct = [each["steamID"] for each in dem_data["gameRounds"][round_num+1]["ctSide"]["players"]]
        # t = [each["steamID"] for each in dem_data["gameRounds"][round_num+1]["tSide"]["players"]]
    # 过滤掉steamid为0的人
    ct = list(filter(lambda num: num != 0, ct))
    t = list(filter(lambda num: num != 0, t))
    return t, ct


def get_player_life_status(player_id,player_side,frame):
    for each in frame[player_side]["players"]:
        if each["steamID"] == player_id:
            return each["isAlive"]


def produce_json(demo_name):
    try:
        path = "/disk3/workspace/stone/5e_demo/"
        #demo_name="g154-20220325013137790770652_de_dust2.dem"
        demo_id = demo_name.strip(".dem")
        demo_id = demo_id.strip("/")
        print("demo_id", demo_id)
        demo_parser = DemoParser(demofile=demo_name,
                                 demo_id=demo_id,
                                 parse_frames=True,
                                 parse_rate=12) # parse_rate means the interval between the sampled tick


        data = demo_parser.parse()
        # data = demo_parser.read_json("./{}.json".format(demo_id))

        # init dump
        players_pov_info = {}
        t, ct = get_all_players(data, 1)
        players_pov_info["players"] = t + ct
        for each in t + ct:
            players_pov_info[each] = {
                        "steamID": each,
                        "map": data["mapName"],
                        "info": []
                    }

        rounds = data["gameRounds"]
        # enumerate rounds
        for r_n, round in enumerate(rounds):
                try:
                    t, ct = get_all_players(data, r_n)
                except:
                    continue
                t_ends, ct_ends = {},{}
                frames = round["frames"]
                start_tick = round["startTick"]
                # enumerate frames per round
                for frame in frames:
                    tick = frame["tick"]
                    for each_player in t:
                        # update end tick when player is alive and round doesn't end
                        if get_player_life_status(each_player,"t",frame):
                            if tick <= round["endOfficialTick"]:
                                end_tick = tick
                                t_ends[each_player] = end_tick
                    for each_player in ct:
                        # update end tick when player is alive and round doesn't end
                        if get_player_life_status(each_player, "ct", frame):
                            if tick <= round["endOfficialTick"]:
                                end_tick = tick
                                ct_ends[each_player] = end_tick
                # put info in the dump
                for each_player in t:
                    players_pov_info[each_player]["info"].append([start_tick, t_ends[each_player],"t"])

                for each_player in ct:
                    players_pov_info[each_player]["info"].append([start_tick, ct_ends[each_player],"ct"])
        with open(path+demo_id+".json", "w") as f:
            f.write(json.dumps(players_pov_info))
            print(path+demo_id+".json", "DONE writting")
    except:
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    name_list = sys.argv[1:]
    print("processing", ",\n".join(name_list))
    list(map(produce_json, name_list))
    # 11847633
    # 14A4A998


