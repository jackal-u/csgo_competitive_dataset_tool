

## description：
this is the tool repository for [csgo competitive dataset](https://www.kaggle.com/datasets/kissjonh/csgo-competitive-dataset) made by stone&stemcell

more specifically,  this is a CS:GO video&action dataset producer that takes demo as input source.



## produce routine

- use dem2ticks.py to produce the tick index for each player in each round per demo
  

  ```json
  # file_name: g151-c-20220325145023354066746_de_dust2.json
  
  {"players": # a list stores all players in this demo
            [76561198275573302, ...the steamid of the rest 9 players ], 
  
  
   "76561198275573302":  # player with this steamid, it's round data
          {"steamID": 76561198275573302, 
           "map": "de_dust2", 
           "info": [[1150, 6097, "t"], ...the rest rounds 
          }, # the info [[start_tick, end_tick, side],...]
   
   
  ...the rest 9 players
  }
  ```
  
  



- recording vids

  - install  [csgo demo manager](https://github.com/akiver/CSGO-Demos-Manager) and [cheat engine](https://github.com/cheat-engine/cheat-engine)

  - use cheat engine to achieve pov lock in game.  [how to video](https://www.youtube.com/watch?v=zFjwrzzvrCQ)

  - configurate the path that stores the json files in script dem2vid.py

  - configurate the buttons pixel location in script dem2vid.py

  - switch demo manager to the start, click focus the 1st demo and run the dem2vid.py

    

- use dem2labels.py to produce labels to each demo

  - python dem2labels.py   ./*.dem                             ( in  linux)

- NOW, you have the dataset


## script description
- dem2tick.py reads the *.dem files stored in ./demo and dump them into ./demo/record_ticks/matchid_mapname.json format.

- dem2vid.py reads the matchid_mapname.json and produce pov video for each player in each round, e.g ./data/g151-c-20220402212855368210429_de_dust2_round1_t_tick_1159_8945_player_76561198146323670.mp4

- dem2label.py reads matchid_mapname.json and infer player action for each player in each round, e.g /labels/g151-c-20220402212855368210429_de_dust2/g151-c-20220402212855368210429_de_dust2_round10_ct_tick_99900_105509_player_76561198417754488.csv

- meta.py match *.mp4 and *.csv label and produce meta.csv for model training.

## note
the labeling requires huge ram space, make sure you have enough.

email: mengshi2022@ia.ac.cn
