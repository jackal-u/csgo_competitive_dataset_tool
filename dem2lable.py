# for demo json structure, see:https://awpy.readthedocs.io/en/latest/parser_output.html
# see the infer logic, see: https://jlucs.atlassian.net/wiki/spaces/JLUCSNB/pages/4063233
import json
import os
import sys
import numpy as np
from awpy.parser import DemoParser


def normalizeAngles(pitch, yaw):
    """
    tick中的瞄准方向并不直觉，这个函数将angle规则化成直觉的角度
    pitch=tick中的ViewY ==>取值[-89,+89]
    yaw=tick中的ViewX ==>取值[-179,+179]
    """
    if pitch > 89:
        pitch -= 360
    if yaw > 180:
        yaw -= 360
    if yaw < -180:
        yaw += 360
    return pitch, yaw


def get_all_players(dem_data, round_num):
    ":return all playerid"
    try:
        ct =[each["steamID"] for each in dem_data["gameRounds"][round_num]["ctSide"]["players"]]
        t = [each["steamID"] for each in dem_data["gameRounds"][round_num]["tSide"]["players"]]
    except:
        pass
    # 过滤掉steamid为0的人
    ct = list(filter(lambda num: num != 0, ct))
    t = list(filter(lambda num: num != 0, t))
    return t, ct


def get_player_life_status(player_id,player_side,frame):
    for each in frame[player_side]["players"]:
        if each["steamID"] == player_id:
            return each["isAlive"]


def gen_fire_dic(data, r_n):
    dic={}
    t,ct = get_all_players(data,r_n)
    # use set to store ticks
    for player in t+ct:
        dic[player] = set()
    # put fire ticks in each player's set
    for each_fire in data["gameRounds"][r_n]["weaponFires"]:
        try:
            dic[each_fire["playerSteamID"]].add(each_fire["tick"])
        except KeyError:
            import traceback
            traceback.print_exc()
            dic[each_fire["playerSteamID"]] = set()
            dic[each_fire["playerSteamID"]].add(each_fire["tick"])
        except:
            import traceback
            traceback.print_exc()

    return dic


def get_player_status_from_frame(frame, side, player_id, status_name):
    for each_player in frame[side]["players"]:
        if each_player["steamID"]!= player_id:
            continue
        return each_player[status_name]


def get_player_location(frame, side, player_id):
    x = get_player_status_from_frame(frame, side, player_id, "x")
    y = get_player_status_from_frame(frame, side, player_id, "y")
    return x, y


def get_rad_tang_speed(frame, side, player):
    v_x = get_player_status_from_frame(frame, side, player, "velocityX")
    v_y = get_player_status_from_frame(frame, side, player, "velocityY")
    if v_x is None:
        v_x = 0
    if v_y is None:
        v_y = 0
    try:
        theta_speed = np.arctan2(v_y, v_x) * 180 / np.pi
    except:
        import traceback
        traceback.print_exc()
        print(v_x, v_y)
    viewX, viewY = get_player_status_from_frame(frame, side, player, "viewX"), get_player_status_from_frame(
        frame, side, player, "viewY")
    if viewX is None:
        viewX = 0
    if viewY is None:
        viewY = 0

    pitch, theta_player = normalizeAngles(viewX, viewY)
    delta_theta = theta_speed - theta_player
    v_norm = np.linalg.norm([v_x, v_y])
    v_radial = v_norm * np.cos(delta_theta)
    v_tangential = v_norm * np.sin(delta_theta)
    return v_radial, v_tangential


def get_aim_angle(frame, side, player):
    """
    tick中ViewY取值：[0,89] [271,360]=normalize=>pitch取值[-89,+89]
    tick中ViewX取值 ： [0,360] =normalize=>yaw取值[-179,+179]
    :param frame:
    :param side:
    :param player:
    :return:
    """
    viewX, viewY = get_player_status_from_frame(frame, side, player, "viewX"), get_player_status_from_frame(
        frame, side, player, "viewY")
    pitch, yaw = normalizeAngles(viewY, viewX)
    return pitch, yaw


def infer_wasd_by_speed(v_radial_0, v_tangential_0,v_radial_1, v_tangential_1):
    w,a,s,d = 0,0,0,0
    # 如果径向速度变大,且为正向速度
    if v_radial_1 - v_radial_0 > 0:
        w = 1
    if v_radial_1 > 10:
        w=1
    # 如果径向速度不变且为正
    if v_radial_1 == v_radial_0 and v_radial_0 > 0:
        w = 1

    # 如果径向速度变小,且为负向速度
    if v_radial_1 - v_radial_0 < 0 and v_radial_1 < 0:
        s = 1
    # 如果径向速度不变且为负
    if v_radial_1 == v_radial_0 and v_radial_0 < 0:
        s = 1

    # 如果切向速度变大,且为正
    if v_tangential_1 - v_tangential_0 > 0 and v_tangential_0 > 0:
        a = 1
    # 如果切向速度不变且正
    if v_tangential_1 == v_tangential_0 and v_tangential_0 > 0:
        a = 1
    # 如果切向速度变小,且为负
    if v_tangential_1 - v_tangential_0 < 0 and v_tangential_0 < 0:
        d = 1
    # 如果切向速度不变且负
    if v_tangential_1 == v_tangential_0 and v_tangential_0 < 0:
        d = 1
    return w,a,s,d


def infer_wasd_by_angle(angle):
    """# angle must be -180 +180"""
    w,a,s,d = 0,0,0,0
    if -5 < angle <= 5:
        d = 1
    if 5 < angle <= 85:
        w = 1
        d = 1
    if 85 < angle <= 95:
        w = 1
    if 95 < angle <= 175:
        w = 1
        a = 1
    if angle >= 175 or angle <= -175:
        a = 1
    if -85 < angle <= -5:
        s = 1
        d = 1
    if -95 < angle <= -85:
        s = 1
    if -175 < angle <= -95:
        a = 1
        s = 1
    return w,a,s,d


def find_nearest_index_from_list(li, value):
    dis = [abs(value-each) for each in li]
    return dis.index(min(dis))


def get_weapon_class(name):
    """
    1 2 3 4 5[主武器，副武器, 刀子, 投掷物, c4]
    :param name:
    :return:
    """
    if not name:
        return 1
    Rifle = ["Nova", "XM1014", "MAG-7", "Sawed-Off", "MAC-10","MP5-SD","MP9", "UMP-45", "MP7", "PP-Bizon", "P90",
             "Galil AR", "FAMAS", "AK-47", "M4A4", "M4A1", "SG 553", "AUG", "SSG 08", "AWP", "G3SG1",
             "SCAR-20", "M249", "Negev"]
    Pistol = ["Glock-18", "P2000", "USP-S", "P250", "Dual Berettas", "Tec-9", "Five-SeveN", "CZ75 Auto", "Desert Eagle"]

    Knife = ["Knife", "Zeus x27"]
    Nades = ["Decoy Grenade", "Flashbang", "HE Grenade", "Smoke Grenade", "Molotov", "Incendiary Grenade"]
    Bomb = ["C4"]
    if name in Rifle:
        return 1
    if name in Pistol:
        return 2
    if name in Knife:
        return 3
    if name in Nades:
        return 4
    if name == "C4":
        return 5
    print("unknown weapon", name)
    return 1


if __name__ == '__main__':
    demo_names = sys.argv[1:]  # "g151-c-20220402212855368210429_de_dust2.dem"
    print("names", demo_names)
    for demo_name in demo_names:
            demo_id = demo_name.strip(".dem")
            demo_id = demo_id.strip("/")
            action_gap = 8  # action之间的tick差；一秒如执行8次行为，在128tick服务器，需要每16tick生成一个aciton
            parse_rate = 1  # 4 为sample出来的tick差距为8tick； 2为sample出来的tick差距为4tick
            infer_tick_len = 4   # 在已经sample后的基础上，把几个tick纳入考虑范围生成action
            mouse_y_possibles = [i for i in range(-89,
                                                  90)] + [0.3*i for i in range(30)] # [-50.0,-40.0,-30.0,-20.0,-18.0,-16.0,-14.0,-12.0,-10.0,-8.0,-6.0,-5.0,-4.0,-3.0,-2.0,-1.0,0.0,1.0,2.0,3.0,4.0,5.0,6.0,8.0,10.0,12.0,14.0,16.0,18.0,20.0,30.0,40.0,50.0]
            mouse_x_possibles = [i for i in range(-179,
                                                  180)] + [0.2*i for i in range(30)] # [-170,-130,-100,-80,-70,-60,-50.0,-40.0,-30.0,-20.0,-18.0,-16.0,-14.0,-12.0,-10.0,-8.0,-6.0,-5.0,-4.0,-3.0,-2.0,-1.0,0.0,1.0,2.0,3.0,4.0,5.0,6.0,8.0,10.0,12.0,14.0,16.0,18.0,20.0,30.0,40.0,50.0,60,70,80,100,130,170]
            print("demo_id", demo_id)
            demo_parser = DemoParser(demofile=demo_name,
                                     demo_id=demo_id,
                                     parse_frames=True,
                                     parse_rate=parse_rate)# parse_rate means the interval between the sampled tick
            data = demo_parser.parse()
            #data = demo_parser.read_json("./{}.json".format(demo_id))
            rounds = data["gameRounds"]
            # enumerate rounds
            for r_n, round in enumerate(rounds):
                try:
                    t_ends, ct_ends = {}, {}
                    fire_sets = gen_fire_dic(data, r_n)
                    t, ct = get_all_players(data, r_n)
                    frames = round["frames"]  # + round["frames"][-8:]
                    #frames = frames + frames[-infer_tick_len:]
                    start_tick = round["startTick"]
                    # t
                    for player in t:
                        # enumerate frames per round
                        labels = []
                        side = "t"
                        for i, frame in enumerate(frames):
                            tick = frame["tick"]
                            clockTime = frame["clockTime"]
                            # 每infer_tick_len tick取一个tick作为action
                            if i % infer_tick_len != 0 or i > len(frames) - infer_tick_len -1:
                                continue
                            # 如果玩家死亡，跳过
                            if not get_player_status_from_frame(frame,side,player,"isAlive"):
                                continue
                            # 当前以及后action_gap tick如果有fire，则True
                            is_fire = 0
                            is_fire_tick = tick
                            for c in range(action_gap):
                                is_fire_tick = is_fire_tick + c
                                if is_fire_tick in fire_sets[player]:
                                    is_fire = 1
                            # 当前以及后infer_tick_len tick如果开镜状态变化，则True
                            is_scope = 0
                            scope_set = set()
                            for c in range(infer_tick_len):
                                is_scoped = get_player_status_from_frame(frames[i + c], side, player, "isScoped")
                                scope_set.add(str(is_scoped))
                            if len(scope_set)!=1:
                                is_scope = 1
                            # 当前以及后3tick如果从不在空中切换为在空中，则True
                            is_jump = 0
                            air_list = []
                            for c in range(infer_tick_len):
                                isAirborne = get_player_status_from_frame(frames[i + c], side, player, "isAirborne")
                                air_list.append(str(int(isAirborne)))
                            if "01" in "".join(air_list):
                                is_jump = 1
                            # 当前以及后3tick如果isDucking或isDuckingInProgress为True，则True
                            is_crouch = 0
                            for c in range(infer_tick_len):
                                isDucking = get_player_status_from_frame(frames[i + c], side, player, "isDucking")
                                isDuckingInProgress = get_player_status_from_frame(frames[i + c], side, player, "isDuckingInProgress")
                                if isDucking or isDuckingInProgress:
                                    is_crouch = 1
                            # 当前walking为True，则True
                            is_walking = int(get_player_status_from_frame(frames[i], side, player, "isWalking"))
                            # 当前以及后7tick如果从未换弹切换为换弹，则True
                            is_reload = 0
                            reload_list = []
                            for c in range(infer_tick_len):
                                isReloading = get_player_status_from_frame(frames[i + c], side, player, "isReloading")
                                reload_list.append(str(int(isReloading)))
                            if "01" in "".join(reload_list):
                                is_reload = 1
                            # 当前以及后7tick如果存在isPlanting或isDefusing为True，则True
                            is_e = 0
                            for c in range(infer_tick_len):
                                isPlanting = get_player_status_from_frame(frames[i + c], side, player, "isPlanting")
                                isDefusing = get_player_status_from_frame(frames[i + c], side, player, "isDefusing")
                                if isDefusing or isPlanting:
                                    is_e = 1
                            ## WASD推断规则
                            # 计算径向切向速度(废止，采用简单逻辑)
                            # v_radial_0, v_tangential_0 = get_rad_tang_speed(frames[i + 1], side, player)
                            # v_radial_1, v_tangential_1 = get_rad_tang_speed(frames[i + 1 + infer_tick_len], side, player)
                            # w, a, s, d = infer_wasd_by_speed(v_radial_0, v_tangential_0, v_radial_1, v_tangential_1)
                            # 获得当前瞄准角度，移动向量
                            pitch_0, yaw_0 = get_aim_angle(frames[i], side, player)
                            x_0, y_0 = get_player_location(frames[i], side, player)
                            x_1, y_1 = get_player_location(frames[i + infer_tick_len], side, player)
                            goto_vec_yaw = np.arctan2(y_1-y_0, x_1-x_0)*180/np.pi
                            goto_on_aim = (goto_vec_yaw - (yaw_0-90))
                            if goto_on_aim > 180:
                                goto_on_aim = goto_on_aim - 360
                            if goto_on_aim < -180:
                                goto_on_aim = goto_on_aim + 360
                            # if tick == 5255 and player == 76561198355750091:
                            #     print("x_0, y_0", x_0, y_0)
                            #     print("x_1, y_1", x_1, y_1)
                            #     print("pitch_0, yaw_0", pitch_0, yaw_0)
                            #     print("goto_vec_yaw", goto_vec_yaw)
                            #     print("goto_on_aim", goto_on_aim)
                                #print("direction_angle", direction_angle)
                            w, a, s, d = infer_wasd_by_angle(goto_on_aim)

                            ## mouse移动规则
                            # 求出delta_pitch(-180,+180)   delta_yaw(-180, +180)
                            pitch_0, yaw_0 = get_aim_angle(frames[i], side, player)
                            pitch_1, yaw_1 = get_aim_angle(frames[i + infer_tick_len], side, player)
                            delta_pitch = pitch_1 - pitch_0
                            delta_yaw = yaw_1 - yaw_0
                            n_delta_pitch, n_delta_yaw = normalizeAngles(delta_pitch, delta_yaw)
                            # if tick == 5255 and player == 76561198355750091:
                            #     print("pitch_0, yaw_0", pitch_0, yaw_0)
                            #     print("pitch_1, yaw_1", pitch_1, yaw_1)
                            #     print("delta_pitch，delta_yaw", delta_pitch, delta_yaw)
                            #     print("n_delta_pitch, n_delta_yaw", n_delta_pitch, n_delta_yaw)

                            # 将delta映射到mouse_possibles
                            mouse_y = find_nearest_index_from_list(mouse_y_possibles, n_delta_pitch)
                            mouse_x = find_nearest_index_from_list(mouse_x_possibles, n_delta_yaw)

                            ## 切换武器规则
                            # weapon name
                            cur_weapon = get_player_status_from_frame(frames[i], side, player, "activeWeapon")
                            next_weapon = get_player_status_from_frame(frames[i + infer_tick_len], side, player, "activeWeapon")
                            # 对比当前tick和后8tick，取值为目标所属类别
                            switch = 0
                            if next_weapon != cur_weapon:
                                switch = get_weapon_class(next_weapon)
                            # stringfy the action
                            action = [clockTime, tick, w, a, s, d, mouse_x, mouse_y, is_fire, is_scope, is_jump, is_crouch, is_walking, is_reload, is_e, switch]
                            action = [str(each) for each in action]
                            action_str = "\t".join(action)

                            # update end tick when player is alive and round doesn't end
                            if get_player_life_status(player, side, frame):
                                if tick <= round["endOfficialTick"]:
                                    end_tick = tick
                                    t_ends[player] = end_tick
                            # append frame
                            labels.append(action_str)

                        if not os.path.isdir("./labels/{}/".format(demo_id)):
                            os.makedirs("./labels/{}/".format(demo_id))

                        with open("./labels/{}/{}_round{}_{}_tick_{}_{}_player_{}.csv".format(demo_id, demo_id, r_n + 1, side,start_tick, end_tick, player),"w") as f:
                            f.write("clockTime,tick,w,a,s,d,mouse_x,mouse_y,is_fire,is_scope,is_jump,is_crouch,is_walking,is_reload,is_e,switch\n".replace(",", "\t"))
                            f.write("\n".join(labels))

                    for player in ct:
                        # enumerate frames per round
                        labels = []
                        side = "ct"
                        for i, frame in enumerate(frames):
                            tick = frame["tick"]
                            clockTime = frame["clockTime"]
                            # 每infer_tick_len tick取一个tick作为action
                            if i % infer_tick_len != 0 or i > len(frames) - infer_tick_len - 1:
                                continue
                            # 如果玩家死亡，跳过
                            if not get_player_status_from_frame(frame, side, player, "isAlive"):
                                continue
                            # 当前以及后7tick如果有fire，则True
                            is_fire = 0
                            is_fire_tick = tick
                            for c in range(action_gap):
                                is_fire_tick = is_fire_tick + c
                                if is_fire_tick in fire_sets[player]:
                                    is_fire = 1

                            # 当前以及后7tick如果开镜状态变化，则True
                            is_scope = 0
                            scope_set = set()
                            for c in range(infer_tick_len):
                                is_scoped = get_player_status_from_frame(frames[i + c], side, player, "isScoped")
                                scope_set.add(str(is_scoped))
                            if len(scope_set)!=1:
                                is_scope = 1
                            # 当前以及后7tick如果从不在空中切换为在空中，则True
                            is_jump = 0
                            air_list = []
                            for c in range(infer_tick_len):
                                isAirborne = get_player_status_from_frame(frames[i + c], side, player, "isAirborne")
                                air_list.append(str(int(isAirborne)))
                            if "01" in "".join(air_list):
                                is_jump = 1

                            # 当前以及后7tick如果isDucking或isDuckingInProgress为True，则True
                            is_crouch = 0
                            for c in range(infer_tick_len):
                                isDucking = get_player_status_from_frame(frames[i + c], side, player, "isDucking")
                                isDuckingInProgress = get_player_status_from_frame(frames[i + c], side, player, "isDuckingInProgress")
                                if isDucking or isDuckingInProgress:
                                    is_crouch = 1
                            # 当前walking为True，则True
                            is_walking = int(get_player_status_from_frame(frames[i], side, player, "isWalking"))
                            # 当前以及后7tick如果从未换弹切换为换弹，则True
                            is_reload = 0
                            reload_list = []
                            for c in range(infer_tick_len):
                                isReloading = get_player_status_from_frame(frames[i + c], side, player, "isReloading")
                                reload_list.append(str(int(isReloading)))
                            if "01" in "".join(reload_list):
                                is_reload = 1
                            # 当前以及后7tick如果存在isPlanting或isDefusing为True，则True
                            is_e = 0
                            for c in range(infer_tick_len):
                                isPlanting = get_player_status_from_frame(frames[i + c], side, player, "isPlanting")
                                isDefusing = get_player_status_from_frame(frames[i + c], side, player, "isDefusing")
                                if isDefusing or isPlanting:
                                    is_e = 1
                            ## WASD推断规则
                            # 计算径向切向速度
                            # v_radial_0, v_tangential_0 = get_rad_tang_speed(frames[i + 1], side, player)
                            # v_radial_1, v_tangential_1 = get_rad_tang_speed(frames[i + 1 + infer_tick_len], side, player)
                            # w, a, s, d = infer_wasd_by_speed(v_radial_0, v_tangential_0, v_radial_1, v_tangential_1)
                            # 获得当前瞄准角度，移动向量
                            pitch_0, yaw_0 = get_aim_angle(frames[i], side, player)
                            x_0, y_0 = get_player_location(frames[i], side, player)
                            x_1, y_1 = get_player_location(frames[i + infer_tick_len], side, player)
                            goto_vec_yaw = np.arctan2(y_1 - y_0, x_1 - x_0) * 180 / np.pi
                            goto_on_aim = (goto_vec_yaw - (yaw_0 - 90))
                            if goto_on_aim > 180:
                                goto_on_aim = goto_on_aim - 360
                            if goto_on_aim < -180:
                                goto_on_aim = goto_on_aim + 360
                            #direction_angle = np.arctan2(np.cos(goto_on_aim), np.sin(goto_on_aim))* 180 / np.pi
                            w, a, s, d = infer_wasd_by_angle(goto_on_aim)
                            ## mouse移动规则
                            # 求出delta_pitch(-180,+180)   delta_yaw(-180, +180)
                            pitch_0, yaw_0 = get_aim_angle(frames[i], side, player)
                            pitch_1, yaw_1 = get_aim_angle(frames[i + infer_tick_len], side, player)
                            delta_pitch = pitch_1 - pitch_0
                            delta_yaw = yaw_1 - yaw_0
                            n_delta_pitch, n_delta_yaw = normalizeAngles(delta_pitch, delta_yaw)

                            # 将delta映射到mouse_possibles
                            mouse_y = find_nearest_index_from_list(mouse_y_possibles, n_delta_pitch)
                            mouse_x = find_nearest_index_from_list(mouse_x_possibles, n_delta_yaw)
                            ## 切换武器规则
                            # weapon name
                            cur_weapon = get_player_status_from_frame(frames[i], side, player, "activeWeapon")
                            next_weapon = get_player_status_from_frame(frames[i + infer_tick_len], side, player, "activeWeapon")
                            # 对比当前tick和后8tick，取值为目标所属类别
                            switch = 0
                            if next_weapon != cur_weapon:
                                switch = get_weapon_class(next_weapon)
                            # stringfy the action
                            action = [clockTime, tick, w, a, s, d, mouse_x, mouse_y, is_fire, is_scope, is_jump, is_crouch, is_walking, is_reload, is_e, switch]
                            action = [str(each) for each in action]
                            action_str = "\t".join(action)
                            # update end tick when player is alive and round doesn't end
                            if get_player_life_status(player, side, frame):
                                if tick <= round["endOfficialTick"]:
                                    end_tick = tick
                                    ct_ends[player] = end_tick
                            # update frame
                            labels.append(action_str)
                        with open("./labels/{}/{}_round{}_{}_tick_{}_{}_player_{}.csv".format(demo_id,demo_id,r_n+1,side,start_tick,end_tick,player), "w") as f:
                            f.write("clockTime,tick,w,a,s,d,mouse_x,mouse_y,is_fire,is_scope,is_jump,is_crouch,is_walking,is_reload,is_e,switch\n".replace(",","\t"))
                            f.write("\n".join(labels))
                except:
                    print("ERROR!! demo {}, round{} failed, skipping it".format(demo_id, r_n))
                    import traceback
                    traceback.print_exc()
                    continue

    os.popen("rm -f ./{}.json".format(demo_id))