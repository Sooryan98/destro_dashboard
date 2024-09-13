#!/usr/bin/env python3

import threading
from queue import PriorityQueue
import multiprocessing
from multiprocessing import Process, Manager, Lock
import socket
import json
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from entity_locations import human_location,robot_location

import time
import asyncio


# Constants
WIDTH, HEIGHT = 2000, 1500
ROWS, COLS = 2000, 1500
# CELL_SIZE = WIDTH // COLS
CELL_SIZE = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

num_robots=16
num_humans=8
# currently robot speed is 1.5 m/s at 0.58 and you can change the value of robot_speed
robot_speed=0.24
human_speed=0.40
loc_size=10

class VisualizationNode():
    def __init__(self):
        
        # self.init_pygame()
        self.run = True
        self.manager = Manager()
        self.robot_map={}
        self.human_map={}
        self.targets = self.manager.dict()
        self.paths = self.manager.dict()
        self.grid = self.create_map(ROWS, COLS, [(19, 17, 117), (28, 17, 36),(37, 17, 36),  (46, 17, 36), (54, 17,36),(64, 17,36), (73, 17, 36), (86, 17,36), (99, 17,36), (108,17,36),(118, 24,29), (126, 24,36), (135,24,29),(143, 24,29), (153, 24,29), (162,24,29),(171, 24,29), (179, 24,29),(188, 24,29)
                                    ,(28,56,38),(37, 56, 38),  (46, 56, 38), (54, 56,38),(64, 56,38), (73, 56, 38), (86, 56,38), (99, 56,38), (108,56,38),(118,56,38), (126, 56,38), (135,56,38),(143, 56,38), (153, 56,38), (162,56,38),(171, 56,38), (179, 56,38),(188, 56,38),
                                    (28,98,36),(37, 98, 36),  (46, 98, 36), (54, 98,36),(64, 98,36), (73, 98, 36), (86, 98,36), (99, 98,36), (108,98,36),(118, 98,36), (126, 98,36), (135,98,36),(143, 98,36), (153, 98,36), (162,98,36),(171, 98,31), (179, 98,31),(188, 98,31)],
                                    
                                    lanes=[(23,10,23,140),(32,10,32,140),(41,10,41,140),(50,10,50,140),(59,10,59,140),(68,10,68,140),(79,10,79,140),(92,10,92,140),(103,10,103,140),(113,10,113,140),(122,10,122,140),(130,10,130,140),(139,10,139,140),(148,10,148,140),(157,10,157,140),(166,10,166,140),(175,10,175,140),(183,10,183,140),(192,10,192,140),
                                           (5,14,250,14),(5,54,250,54),(5,96,250,96),(5,140,250,140)])
        self.robots, self.humans = self.place_entities(self.grid, 16, 8)
        
        self.start_time=0
        self.end_time=0
        self.failure_chart={}
        self.step_ind={}
       
        self.fastapi_app = FastAPI()
        self.finished_robot=[]
      
        @self.fastapi_app.post("/send_command")
        async def send_command(command: dict):
            try:
                command_json = json.dumps(command)
                command_temp=command
                current_type=command_temp.get('type')

            except Exception as i:
                return {f"{command.get('type')}_{command.get('id')}":"FAIL","DESCRIPTION":f"{i}"}
            try :
                if current_type=='robot':
                    
                    current_id=command_temp.get('id')
                    if current_id>=0 and current_id< num_robots:
                        current_loc=command_temp.get('location')
                        if current_loc in robot_location:
                            if self.robot_map[f'robot_{current_id}']==current_loc:
                                return {f"{current_type}_{current_id}":"SUCCESS"}
                            else:
                                self.listener_callback(command_json)
                                if f"{current_type}_{current_id}" in self.failure_chart:
                 
                                    response= self.failure_chart.pop(f"{current_type}_{current_id}")
                                    if "DESCRIPTION" in response:
                                        descrip=response.get("DESCRIPTION")
                                        return {f"{current_type}_{current_id}":"FAIL","DESCRIPTION":descrip}
                                    else:
                                        return{f"{current_type}_{current_id}":"FAIL","DESCRIPTION":"No info provided."}

                                await self.target_check(command.get('type'),command.get('id'),command.get('location'))
                                # self.end_time=time.perf_counter()
                                # elapsed_time=self.end_time-self.start_time
                                return {f"{current_type}_{current_id}":"SUCCESS"}
                        else:
                            return {f"{current_type}_{current_id}": "FAIL", "DESCRIPTION": "Requested location is not defined in dictionary"}
                    else:
                        return {f"{current_type}_{current_id}": "FAIL", "DESCRIPTION": f"Robot ID does not exist please use robot ids between 0 and {num_robots-1}"}

                elif current_type=='human':
                    current_id=command_temp.get('id')
                    if current_id>=0 and current_id<num_humans:

                        current_loc=command_temp.get('location')
                        if current_loc in human_location:
                            if self.human_map[f'human_{current_id}']==current_loc:
                                return {f"{current_type}_{current_id}":"SUCCESS"}
                            else:
                                self.listener_callback(command_json)

                                await self.target_check(command.get('type'),command.get('id'),command.get('location'))
                
                                return {f"{current_type}_{current_id}":"SUCCESS"}
                        else:
                            return {f"{current_type}_{current_id}": "FAIL", "DESCRIPTION": "Requested location is not defined in dictionary"}
                    else:
                        return {f"{current_type}_{current_id}": "FAIL", "DESCRIPTION": f"Human ID does not exist please use robot ids between 0 and {num_humans-1}"}

                else :
                    return {f"{current_type}": "FAIL", "DESCRIPTION": "The requested type doesnt exist"}

       
                
            except Exception as e:
                # raise HTTPException(status_code=500, detail=str(e))
                if f"{current_type}_{current_id}" not in self.failure_chart:
                    self.failure_chart[f"{current_type}_{current_id}"]={"DESCRIPTION":f"{e}"}
                # return {f"{current_type}_{current_id}":"FAIL","DESCRIPTION":f"{e}"}
        self.fastapi_thread = threading.Thread(target=self.start_fastapi_server)
        self.fastapi_thread.start()
        self.lock = Lock()

    async def target_check(self,entity_type,entity_id,location):
        while True:
            if entity_type=='robot':
                if f'robot_{entity_id}' in self.finished_robot:
                    x,y=robot_location.get(f"{location}")
                    if self.robots[entity_id]==(x,y):
                        self.finished_robot.remove(f'robot_{entity_id}')
                        break
            if entity_type=='human':
                if f'human_{entity_id}' in self.finished_robot:
                    x,y=human_location.get(f"{location}")
                    if self.humans[entity_id]==(x,y):
                        self.finished_robot.remove(f'human_{entity_id}')
                        break
            await asyncio.sleep(0.1)


    def create_map(self, rows, cols, walls,lanes):
        grid = [[0.5 for _ in range(cols)] for _ in range(rows)]
        for row in range(ROWS):
            for col in range(COLS):
                if row <=16:
                    grid[row][col]=0
        for x, y_start, length in walls:
            for i in range(length):
                if y_start + i < rows:
                    grid[y_start + i][x] = 1
        for (x_start, y_start, x_end, y_end) in lanes:
            for x in range(x_start, x_end + 1):
                for y in range(y_start, y_end + 1):
                    if 0 <= x < cols and 0 <= y < rows:
                        grid[y][x] = 0
                    
        return grid

    
    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def astar(self, grid, start, goal,ptype):
        
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        close_set = set()
        came_from = {}
        gscore = {start: 0}
        fscore = {start: self.heuristic(start, goal)}
        oheap = PriorityQueue()
        oheap.put((fscore[start], start))

        while not oheap.empty():
            current = oheap.get()[1]

            if current == goal:
                data = []
                while current in came_from:
                    data.append(current)
                    current = came_from[current]
                return data[::-1]

            close_set.add(current)
            for i, j in neighbors:
                neighbor = current[0] + i, current[1] + j
                tentative_g_score = gscore[current] + 1

                if 0 <= neighbor[0] < len(grid[0]) and 0 <= neighbor[1] < len(grid):
                    if ptype=='robot':
                        if grid[neighbor[1]][neighbor[0]] == 1 or grid[neighbor[1]][neighbor[0]]==0.5:
                            continue
                    else :
                        if grid[neighbor[1]][neighbor[0]] == 1 :
                            continue

                else:
                    continue

                if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                    continue

                if tentative_g_score < gscore.get(neighbor, 0) or neighbor not in [i[1] for i in oheap.queue]:
                    came_from[neighbor] = current
                    gscore[neighbor] = tentative_g_score
                    fscore[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    oheap.put((fscore[neighbor], neighbor))
        return []

    def place_entities(self, grid, num_robots, num_humans):
        # robot_start=[(23,10),(32,10),(41,10),(50,10),(59,10),(68,10),(79,10),(92,10),(103,10),(113,10),(122,10),(130,10),(139,10),(148,10),(157,10),(175,10)]
        robot_start=[(146,5),(148,5),(150,5),(152,5),(162,5),(164,5),(166,5),(168,5),
                     (146,10),(148,10),(150,10),(152,10),(162,10),(164,10),(166,10),(168,10)]

        human_start=[(32,54),(79,54),(113,54),(148,54),(32,96),(79,96),(113,96),(148,96)]
        robots = {i: robot_start[i] for i in range(num_robots)}
        humans = {i: human_start[i] for i in range(num_humans)}
        for i in range(num_robots):
            self.robot_map[f'robot_{i}']=robot_start[i]
        for i in range(num_humans):
            self.human_map[f'human_{i}']=human_start[i]
        return robots, humans

    def move_entity(self, entity_type, entity_id, target_x, target_y):
        if entity_type == 'robot':
            self.targets[f'robot_{entity_id}'] = (target_x, target_y)
            process = Process(target=self.pathfinding_process, args=(self.grid, self.robots[entity_id], self.targets[f'robot_{entity_id}'], self.paths, f'robot_{entity_id}',entity_type))
            process.start()
            print(f"Moving {entity_type}_{entity_id}")
        elif entity_type == 'human':
            self.targets[f'human_{entity_id}'] = (target_x, target_y)
            process = Process(target=self.pathfinding_process, args=(self.grid, self.humans[entity_id], self.targets[f'human_{entity_id}'], self.paths, f'human_{entity_id}',entity_type))
            process.start()
        process.join()
        self.step_ind[f'{entity_type}_{entity_id}'] = 0 
        
        # self.draw()

    def pathfinding_process(self, grid, start, goal, paths, key, ptype):
        path = self.astar(grid, start, goal,ptype)
        with self.lock:
            print(f"path len is {len(path)}")
            print(f"Starting time is {self.start_time}")
            paths[key] = path

    def listener_callback(self, msg):
        try:
            if isinstance(msg, str):
                command = json.loads(msg)
            else:
                command = json.loads(msg.data)
            entity_type = command.get('type')
            entity_id = command.get('id')
            location=command.get('location')
            if entity_type=='robot':
                target_x,target_y=robot_location.get(f"{location}")
                print(f"Received COmmand for : {entity_type}_{entity_id}")
                
            else:
                target_x,target_y=human_location.get(f"{location}")
          

            if entity_type and entity_id is not None and target_x is not None and target_y is not None:
                self.start_time=time.perf_counter()
                self.move_entity(entity_type, entity_id, target_x, target_y)
            else:
                print('Invalid command Format')
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON{e}")
        except Exception as e:
            print(f'Error processing command{e}')

    def start_fastapi_server(self):
        uvicorn.run(self.fastapi_app, host='localhost', port=8011)

    def main(self):
        try:
            while self.run:
 

                for entity in list(self.paths.keys()):
                
                    try:
                        if entity in self.paths:
                        
                            if self.step_ind.get(entity,0) < len(self.paths[entity]):
                                if 'robot' in entity:
                                    robot_id = int(entity.split('_')[1])
                                    # print(f'{robot_id}')
                                    self.robots[robot_id] = self.paths[entity][int(self.step_ind[entity])]
                                    self.step_ind[entity]+=robot_speed
                                    # print(f"Robot_{robot_id} is moving")
                                elif 'human' in entity:
                                    human_id = int(entity.split('_')[1])
                                    self.humans[human_id] = self.paths[entity][int(self.step_ind[entity])]
                                    self.step_ind[entity] +=human_speed
                    except KeyError as k:
                        # printing as KEY ERRO
                        if f"{entity}" not in self.failure_chart:
                            self.failure_chart[entity]={"DESCRIPTION":f"Key Error 1 for{k}"}
                     
                time.sleep(0.1)

                completed = []
                
                for key in self.targets.keys():
                    
                    entity_id = int(key.split('_')[1])
                    target = self.targets[key]
                    if 'robot' in key and self.robots[entity_id] == target:
                        
                        for nam,val in robot_location.items():
                            
                            if val== target:
                                target_name=nam
                                if f'robot_{entity_id}' in self.robot_map:
                                    self.robot_map[f'robot_{entity_id}']=val
                        completed.append(key)
                        print(f"Robot {key} has reached {target}")
                        self.finished_robot.append(key)
                    elif 'human' in key and self.humans[entity_id] == target:
                        for nam,val in human_location.items():
                            if val== target:
                                target_name=nam
                                if f'human_{entity_id}' in self.human_map:
                                    self.human_map[f'human_{entity_id}']=val
                        completed.append(key)
                        self.finished_robot.append(key)
                try:
            
                    for key in completed:
                        if key in self.paths:
                            del self.paths[key]
                        if key in self.targets:
                            del self.targets[key]
                        if key in self.step_ind:
                            del self.step_ind[key]
                except KeyError as k:
                    if f"{entity}" not in self.failure_chart:
                            self.failure_chart[entity]={"DESCRIPTION":f"Key Error 2 for {k}"}
                    # print(f'KEY FAULT{k}')
                    
                if not self.paths:
                    self.step_ind = {}

        except KeyboardInterrupt:
            # pygame.quit()
            print("The program is closing")
        finally:
            self.run = False

# def main(args=None):
#     # rclpy.init(args=args)
#     visualization_node = VisualizationNode()
#     visualization_node.main()
#     rclpy.shutdown()

if __name__ == '__main__':
    node=VisualizationNode()
    node.main()
