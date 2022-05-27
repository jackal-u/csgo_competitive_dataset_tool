import json
import time, os, json, keyboard
from pynput.keyboard import Key, Controller
import pyautogui, win32gui
import pymem
import pyperclip
import win32process


# 影片按钮位置(x=741, y=57)
# start_tick位置 (x=888, y=338)
# end_tick位置 (x=1175, y=340)
# 录制参数位置 (x=460, y=714)
# 视频质量位置 (x=132, y=674)
# 生成按钮位置 (x=137, y=56)
# 生成按钮位置 (x=137, y=56)
# 聚焦玩家按钮位置 (x=678, y=376)
# 输出文件名称位置 (x=1187, y=267) 可用于获取demo名字，更改输出文件名字
# 初始页第一栏位置 (x=677, y=237) 用于滚动至下一个
# CFG位置 (x=1853, y=320)


keyboard = Controller()
def change_pov_lock(steam_id):
    """
    借助demomanager的外挂代码，实现按照steamid锁定DEMO pov
    CE扫描找到复选框的地址(会变)
    但是复选框的访问，在软件不关的情况下不会变
    只需要在点击访问后的几秒内，录制开始前，更改访问变量的值为目标值便可
    :param steam_id:
    :return:
    """
    # 获得窗口句柄
    window_handle = win32gui.FindWindow(None, u"CSGO DEMOS MANAGER")
    process_id = win32process.GetWindowThreadProcessId(window_handle)
    handle = pymem.Pymem()
    handle.open_process_from_id(process_id[1])

    pointer_address = 0x17929CCB  # how2find tutorial: https://www.cnblogs.com/LyShark/p/10799926.html#_label4
    # steam_id_address = handle.read_bytes(pointer_address, 4)
    # steam_id_address = int.from_bytes(steam_id_address, byteorder='little') + 0x8
    # print("old steamid is  ", handle.read_longlong(steam_id_address))
    handle.write_longlong(pointer_address, steam_id)
    print("changed demo_manager pov lock to ", handle.read_longlong(pointer_address))


def bind_pov_lock(steam_id):
    """
    绑定指定steamid为目标按键 每0.1秒按一下
    :param steam_id:
    :return:
    """
    click_to((1853, 320))
    # 写入新的内容
    message = """
    cl_draw_only_deathnotices 1
    cl_clock_correction 0
    snd_musicvolume 0
    mirv_fix playerAnimState 1
    mirv_streams record matPostprocessEnable 1
    mirv_streams record matDynamicTonemapping 1
    mirv_streams record matMotionBlurEnabled 0
    mirv_streams record matForceTonemapScale 0
    net_graph 0
    bind "i"  "spec_player_by_accountid  {}"
              """.format(steam_id)
    type_content(message)


def pause_till_finish(process_name, is_press=False):
    "在指定进程结束时，跳出"
    old_handle = win32gui.FindWindow(None, process_name)
    while 1:
        window_handle = win32gui.FindWindow(None, process_name)
        if old_handle!=0 and window_handle==0:
            print(process_name, "ended")

            return True
        else:
            if is_press:
                #print("switching pov")
                keyboard.press('i')
                time.sleep(0.01)
                keyboard.release('i')
                pass

        old_handle = window_handle


def pause_till_start(process_name, is_press=False, max_wait=30):
    "在指定进程开始时，跳出"
    t0 = time.time()
    old_handle = win32gui.FindWindow(None, process_name)
    while 1:
        window_handle = win32gui.FindWindow(None, process_name)
        if old_handle==0 and window_handle!=0:
            print(process_name, "started")
            return True
        elif time.time()-t0 > max_wait:
            print(process_name, "max time reached , skipping")
            return False
        else:
            time.sleep(0.1)
        old_handle = window_handle

# while True:
#     print(pyautogui.position())
#     time.sleep(1)

def click_to(location):
    pyautogui.moveTo(location)
    time.sleep(0.5)
    pyautogui.click()


def type_content(content):
    # select all
    pyautogui.hotkey("ctrl", "a")
    # delete
    pyautogui.hotkey("ctrl", "x")
    # type
    pyautogui.typewrite(message=content, interval=0.005)


def get_content():
    # select all
    pyautogui.hotkey("ctrl", "a")
    # copy
    pyautogui.hotkey("ctrl", "c")
    # read clipboard
    content = pyperclip.paste()
    return content


def go_back(times):
    for i in range(times):
        pyautogui.hotkey("ctrl", "b")
        time.sleep(1)


def scroll_next(n):
    click_to((677, 237))
    for i in range(n):
        pyautogui.press("down")


def record():
    # 录制代码
    # 首先确定你在录像主页面，点选了第一个
    for i in range(100):
        time.sleep(3)
        pyautogui.hotkey("ctrl", "s")  # 分析当前录像
        time.sleep(13)
        pyautogui.hotkey("ctrl", "d")  # 切入详情
        time.sleep(2.5)
        click_to((741, 57))  # 点选影片
        time.sleep(2.5)
        # 输入视频像素类型参数
        click_to((460, 714))
        type_content("-pix_fmt yuv420p")
        # 改变视频录制质量
        click_to((132, 674))
        type_content(str(vid_quality))
        # 聚焦玩家
        # 获取当前比赛demo名称
        click_to((1187, 267))
        demoid = get_content()

        # 读取json文件
        all_json = os.listdir(demo_json_path)
        if demoid+".json" in all_json:
            with open(demo_json_path+"\\"+demoid+".json", "r") as f:
                obj = json.loads(f.read())
                print(obj)
            players = obj["players"]
            for player in players:
                ## 录制player视频
                # 获取round_tick_list
                print(obj[str(player)])
                round_tick_list = obj[str(player)]["info"]
                for n, round_tick in enumerate(round_tick_list):
                    # 录制round视频
                    start_tick, end_tick, side = round_tick[0], round_tick[1], round_tick[2]
                    round_num = n+1
                    vid_name = demoid+"_round{}_{}_tick_{}_{}_player_{}".format(round_num, side, start_tick, end_tick, player)
                    # 更改文件名称
                    click_to((1187, 267))
                    type_content(vid_name)
                    print("changing vid name to", vid_name)
                    # 更改开始、结束tick
                    click_to((888, 338))
                    type_content(str(start_tick))
                    click_to((1175, 340))
                    type_content(str(end_tick))

                    bind_pov_lock(player)

                    # 点击开始
                    click_to((137, 56))
                    ## 每1秒查询CSGO和CMD 阻塞等待结束
                    # 等待CSGO开始,选服务器
                    pause_till_start(u"Counter-Strike: Global Offensive")
                    time.sleep(1.4)
                    pyautogui.press("enter")
                    time.sleep(1.4)
                    pyautogui.press("enter")

                    pause_till_start(u"Counter-Strike: Global Offensive - Direct3D 9", True)
                    # # 在游戏启动时，STEAMID变量注入前更改访问变量来锁定玩家
                    # change_pov_lock(player)
                    time.sleep(1.4)
                    pyautogui.press("enter")
                    pause_till_finish(u"Counter-Strike: Global Offensive - Direct3D 9", True)
                    time.sleep(1)
                    if not pause_till_start(r"C:\Users\37002\AppData\Local\AkiVer\hlae\ffmpeg\bin\ffmpeg.exe"):
                        continue
                    pause_till_finish(r"C:\Users\37002\AppData\Local\AkiVer\hlae\ffmpeg\bin\ffmpeg.exe")
        else:
            print("going back! ")
            go_back(3)
            scroll_next(i+1)


if __name__=="__main__":
    # 参数
    vid_quality = 30
    demo_json_path = r"D:\data_bak\demo\demo_json"
    time.sleep(1)
    record()
