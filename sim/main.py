
import time, random, math
from operator import attrgetter
import pygame
import io
from urllib.request import urlopen
from colour import Color

class Universe:
    def __init__(self,
            size_x = 10,
            size_y = 10,
            ):
        print('initialising Universe')
        self.size_x = size_x
        self.size_y = size_y
        self.time = 0
        self.blank_universe()
        self.life = []

    # make as set of rowws with cells
    def blank_universe(self):
        self.rows = []
        for x in range(0, self.size_x):
            row = []
            for y in range(0, self.size_y):
                # print(f"x,y = {x}, {y}")
                cell = Cell(self, x,y)
                row.append(cell)
            self.rows.append(row)

    def populate(self):
        # print('populating')
        if self.time == 1:
            #print('spawning grass')
            mid_x = round(self.size_x/2)-1
            mid_y = round(self.size_y/2)-1
            self.rows[mid_x][mid_y].seed_grass()
        if self.time == 10:
            #print('spawning cow')
            self.random_cell().spawn_cow()
        # print('done populating')

    # cycle all the cells
    def cycle(self):
        self.time += 1
        self.populate()
        for x in range(0, self.size_x):
            for y in range(0, self.size_y):
                #print(f'[{x},{y}]', end='')
                self.rows[x][y].cycle()
        #print('done cycling')

    def print(self, window):
        for x in range(0, self.size_x):
            for y in range(0, self.size_y):
                print(self.rows[x][y].render(x, y, window), end='')
            print()

    def random_cell(self):
        return random.choice(random.choice(self.rows))

    def move_organism(self, organism, new_cell=False):
        #print("moving!")
        if not new_cell:
            new_cell = random.choice(organism.neighbours)
        old_cell = organism.cell
        organism.cell = new_cell
        organism.neighbours = new_cell.neighbours()
        old_cell.life.remove(organism)
        new_cell.life.append(organism)


class Cell:

    def __init__(self, universe, x, y
            ):
        self.universe = universe
        self.x = x
        self.y = y
        self.life = []
        self.fertility = 20
        # todo

    # create a string representing my cell
    def render(self, x, y, window):
        text = ["  "]
        for life in self.life:
            text.append(life.render(x, y, window))
        full = ''.join(text)[-3:]
        full += '.'
        return full[0:3]

    # return a list of neighbours
    def neighbours(self):
        n = []
        for x in range(max([0,self.x-1]), min([self.universe.size_x,self.x+2])):
            for y in range(max([0,self.y-1]), min([self.universe.size_y,self.y+2])):
                if x != self.x or y != self.y:
                    n.append(self.universe.rows[x][y])
        return n

    def seed_grass(self):
        self.life.append(Grass(self))

    def spawn_cow(self):
        self.life.append(Cow(self))

    def life_by_type(self, org_type):
        for org in self.life:
            if type(org) == org_type:
                return org

    def grass_height(self):
        grass = self.life_by_type(Grass)
        return grass.height if grass else  0

    def cycle(self):
        for life in self.life:
            life.cycle()


class Organism():
    def __init__(self, cell):
        self.cell = cell
        self.birthday = cell.universe.time
        self.age = 0
        self.neighbours = self.cell.neighbours()
        self.last_cycled = cell.universe.time -1
        self.alive = True
        cell.universe.life.append(self)

    # find a random empty cell next to this one
    def find_empty_neighbouring_cell(self):
        def empty_cell(cell):
            return len(cell.life) == 0
        empty = list(filter(empty_cell, self.neighbours))
       # print(f'boo {len(empty)} empty cells')
        return random.choice(empty) if len(empty) else False

    def find_best_neighbouring_cell(self):
        best_cell = False
        best_rank = 0
        for cell in self.neighbours:
            rank = self.rank_cell(cell)
            if rank > best_rank: # todo cope better with a draw
                best_cell = cell
                best_rank = rank
       # print(f"best rank is {best_rank} at {best_cell.x},{best_cell.y}" if best_rank else "it all sux")
        return best_cell


    # rate each cell in terms of desirability for motion
    def rank_cell(self, cell):
        return 5
        #+ grass height

    def cycle(self):
        if self.alive and self.last_cycled < self.cell.universe.time:
            self.age += 1
            self.live()
            self.reproduce()
            self.last_cycled = self.cell.universe.time

    def __repr__(self):
        return self.__str__()
    def plot_size(self):
        return 5
    def plot_marker(self):
        return 'o'
    def plot_color(self):
        return 'gray'

class Grass(Organism):
    def __init__(self, cell, height = 20):
        super().__init__(cell)
        self.height = height
        #print(f"grass started at {self.height}")

    def live(self):
        # print(f'cycling {self}')
        growth = self.cell.fertility/5
        self.height += growth if self.height < 100 else 0

    def reproduce(self):
        if self.height > 50:
            target = self.find_empty_neighbouring_cell()
            if target:
                target.seed_grass()
                self.height -= 20
                # print ("we made new grass, woot")
    def render(self, x, y, window):
        rgb = []
        i = 0
        for a in list(Color("brown").range_to(Color("green"), 40)):
            rgb.insert(i, [])
            for b in Color.get_rgb(a):
                rgb[i].append(round(b * 255))
            i += 1

        pygame.draw.rect(window, rgb[int(self.height)-1], (x*40, y*40, 40, 40)) if self.height <= 40 else pygame.draw.rect(window, rgb[39], (x*40, y*40, 40, 40))
        return('M' if self.height > 40 else 'm' if self.height > 22 else ',')
    def __str__(self):
        return(f'grass {self.height}')
    def plot_size(self):
        return math.sqrt(self.height)*10
    def plot_marker(self):
        return 'v'
    def plot_color(self):
        return 'green'


class   Cow(Organism):
    def __init__(self, cell):
        super().__init__(cell)
        self.hunger = 100
        self.thirst = 100
        self.reach = 1

    def live(self):
        self.hunger -= 5
        if self.cell.grass_height() < 10:
            self.cell.universe.move_organism(self, self.find_best_neighbouring_cell())
        else:
            self.hunger += 10
            self.cell.life_by_type(Grass).height -= 10

        if self.thirst < 1 or self.hunger < 1 or self.age > 50:
            print("RIP cow")
            self.alive = False

    def rank_cell(self, cell):
        return cell.grass_height()

        #print(f"The cow is {self.cell.universe.time - self.birthday} cycles old, status:{self.hunger}:{self.thirst}")
    def reproduce(self):
        #print(f"i'm {self.hunger} hungry")
        if self.age > 9 and self.hunger > 75 and len(self.cell.life):
            self.cell.spawn_cow()
            print("cow is born")
            self.hunger =- 0
    def render(self, x, y, window):
        if self.alive:
            image_file = io.BytesIO(urlopen("https://thumbs.dreamstime.com/t/cute-simple-cow-vector-graphic-icon-cartoon-cow-animal-square-face-web-print-illustration-example-milk-products-cute-126091010.jpg").read())
        else:
            image_file = io.BytesIO(urlopen("http://i.ebayimg.com/00/s/OTYwWDEyMDI=/z/ZbgAAOSwEK9T5Cr1/$_57.JPG").read())
        image = pygame.transform.scale(pygame.image.load(image_file), (30, 30))
        window.blit(image, (x*40+5, y*40+5))
        return('C' if self.alive else '+')

    def __str__(self):
        return(f'cow {self.hunger}:{self.thirst}')

    def plot_size(self):
        return 100
    def plot_marker(self):
        return 'o'
    def plot_color(self):
        return 'black'

def main():
    pygame.init()
    clock = pygame.time.Clock()
    pygame.display.set_caption("SquareSim")
    print("Simulation started")
    xsize = 10
    ysize = 10
    window = pygame.display.set_mode((xsize*40,ysize*40))
    universe = Universe(xsize,ysize)
    cycle = 1;
    window.fill((0,255,255))
    while True:
        event = pygame.event.poll()
        if event.type == pygame.QUIT:
            break
        if event.type == pygame.KEYDOWN:
            print(f"time is {universe.time}")
            print(f"cycle -  {cycle}")
            if event.key == pygame.K_SPACE:
                window.fill((0,255,255))
                cycle = cycle + 1
                universe.cycle()
                universe.print(window)
                print(f"time is {universe.time}")
        pygame.display.update()
        #clock.tick(60)
    pygame.quit()
    print("Simulation complete")

if __name__ == "__main__":
    main()
