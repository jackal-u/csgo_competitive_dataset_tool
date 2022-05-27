

## description：
a CS:GO video&action data set producer that uses demo as input



## produce routine

- use dem2ticks.py to produce the tick index for each player in each round per demo
  

  ```json
  # file_name: g151-c-20220325145023354066746_de_dust2.json
  
  {"players": 
            [76561198275573302, ...the steamid of the rest 9 players ], 
  
  "76561198275573302": 
          {"steamID": 76561198275573302, 
           "map": "de_dust2", 
           "info": [[1150, 6097, "t"], ...the rest rounds with start_tick, end_tick, side 
          }
  ...the rest 9 players
  }
  ```

  



- recording vids

  - install  [csgo demo manager](https://github.com/akiver/CSGO-Demos-Manager) and [cheat engine](https://github.com/cheat-engine/cheat-engine)

  - use cheat engine to achieve pov lock in game.  [how to video](https://www.youtube.com/watch?v=zFjwrzzvrCQ)

  - config the path that stores the json files in script dem2vid.py

  - config the buttons pixel location in script dem2vid.py

  - switch demo manager to the start, click focus the 1st demo and run the dem2vid.py

    

- use dem2labels.py to produce labels to each demo

  - python dem2labels.py   ./*.dem                             ( in  linux)

- NOW, you have the dataset


## note
the labeling requires huge ram space, make sure you have enough.

email: 370025263@qq.com
