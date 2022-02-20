import asyncio
from collections import deque, defaultdict
from random import choice, randint
from itertools import product as P

click_queue = deque()
flag_queue = deque()

X = lambda a, b: a.intersection(b)
U = lambda a, b: a.union(b)

class Region:
    def __init__(self, pos, neg, total):
        self.pos = pos
        self.neg = neg
        self.union = U(pos, neg)
        self.total = total
        
    def check(self, other, sub = 0):
        if sub: return U(X(self.pos, other.neg), X(self.neg, other.pos))
        return U(X(self.pos, other.pos), X(self.neg, other.neg))
    
    def add(self, other, sub = 0):
        npos, nneg = self.pos-set(), self.neg-set()
        if sub:
            for i in other.pos:
                if i in self.pos: npos.remove(i)
                else: nneg.add(i)
            for i in other.neg:
                if i in self.neg: nneg.remove(i)
                else: npos.add(i)
        else:
            for i in other.pos:
                if i in self.neg: nneg.remove(i)
                else: npos.add(i)
            for i in other.neg:
                if i in self.pos: npos.remove(i)
                else: nneg.add(i)
        return Region(npos, nneg, self.total+(1-2*sub)*other.total)

    def resolve(self):
        reduced = []
        if len(self.pos) == self.total:
            for i in self.pos:
                reduced.append(Region({i}, set(), 1))
            for i in self.neg:
                reduced.append(Region({i}, set(), 0))
        elif self.total == 0 and len(self.neg) == 0:
            for i in self.pos:
                reduced.append(Region({i}, set(), 0))
        return reduced

    def __repr__(self):
        return f'{self.pos} {self.neg} {self.total}'

delta = list(P((0, -1, 1), repeat = 2))[1:]

async def bot(board, X, Y, M, depth_lim, loop_lim = 4, disp = 0):
    global click_queue, flag_queue
    flags, clicks = set(), set()
    regions = []
    meta = {'set() set() 0'}
    lookup = defaultdict(list)
    for x, y in P(range(X), range(Y)):
        if board[y][x] in '12345678':
            sq = set()
            val = int(board[y][x])
            for dx, dy in delta:
                if 0 <= x+dx < X and 0 <= y+dy < Y:
                    if board[y+dy][x+dx] == '-1': sq.add((x+dx, y+dy))
                    elif board[y+dy][x+dx] == 'F': val -= 1
            reg = [Region(sq, set(), val)]
            if str(reg[0]) not in meta:
                regions.append(reg)
                for i in sq: lookup[i].append(reg)
                meta.add(str(reg[0]))
    loops = 1
    while True:
        if disp: print(f'Loop {loops}: {len(regions)} regions')
        for i in regions:
            for j in i[0].resolve():
                if j.total: flags.add(j.pos.pop())
                else: clicks.add(j.pos.pop())
        loops += 1
        if clicks or flags: break
        if (loops > 3 and len(regions) > depth_lim) or loops > loop_lim: break
        new = []
        for i in regions:
            for sq in i[0].union:
                for j in lookup[sq]:
                    if i[0].total > j[0].total: a, b = i[0], j[0]
                    else: a, b = j[0], i[0]
                    if not a.check(b):
                        reg = [a.add(b)]
                        if str(reg[0]) not in meta:
                            new.append(reg)
                            meta.add(str(reg[0]))
                    if not a.check(b, 1):
                        reg = [a.add(b, 1)]
                        if str(reg[0]) not in meta:
                            new.append(reg)
                            meta.add(str(reg[0]))
        for i in new:
            regions.append(i)
            for sq in i[0].union: lookup[sq].append(i)
    if clicks or flags:
        for i in clicks: click_queue.append(i)
        for i in flags: flag_queue.append(i)
        if disp:
            print("Clicks:", clicks)
            print("Flags:", flags)
            print()
    else: await guess(board, regions, lookup, X, Y, M)

async def guess(board, regions, lookup, X, Y, M, disp = 0):
    global click_queue, flag_queue
    if lookup:
        #TODO
        click_queue.append(choice(list(lookup)))
    else:
        unknown = []
        for x, y in P(range(X), range(Y)):
            if board[y][x] == '-1': unknown.append((x,y))
        click_queue.append(choice(unknown))
    if disp: print("Guess:", click_queue)
