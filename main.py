import random
import math
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color,Ellipse,Rectangle,InstructionGroup,Line,RoundedRectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.scatter import Scatter
from kivy.animation import Animation
import uuid

GROWTH = 2

RCOLORS = [
    {'rgba': (.2,.8,.2,1),'hex': '33CC33'},
    {'rgba': (1,.6,0,1),'hex': 'FF9900'},
    {'rgba': (.8,.2,.8,1),'hex': 'CC33CC'},
    {'rgba': (.2,.6,1,1),'hex': '3399FF'}
]

def crossover(p1,p2):
    return "".join(sorted(random.choice(p1)+random.choice(p2)))

class plantmodel:
    counter = 0
    def __init__(self,colorgenes="Rr",heightgenes="Tt",parents=None,test=None):
        self.id = str(uuid.uuid4())[:8]
        self.parents = parents
        self.test = test

        self.colorgenes = "".join(sorted(colorgenes))
        self.heightgenes = "".join(sorted(heightgenes))
        self.age = 0
        self.planted = False
        self.harvestable = False
        self.pollinator = None

    @property
    def phenocolor(self):
        return (.9,.1,.1,1) if "R" in self.colorgenes else (1,1,1,1)

    @property
    def phenoheight(self):
        return 1.4 if "T" in self.heightgenes else .8

    def update(self,dt):
        if self.planted and self.age < 30:
            self.age += dt*GROWTH
            if self.age >= 30:
                self.harvestable = True

class plantwidget(Widget):
    def __init__(self,model,**kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.size = (80,80)
        self.size_hint = (None,None)

        self.genelabel = Label(text=f"{self.model.colorgenes}\n{self.model.heightgenes}",color=(1,1,1,.7),font_size="10sp",halign="center",markup=True)
        self.add_widget(self.genelabel,index=967)

        self.canvasthing = InstructionGroup()
        self.canvas.add(self.canvasthing)
        Clock.schedule_interval(self.update,1/30)

    def update(self,dt):
        self.model.update(dt)
        self.canvasthing.clear()
        self.genelabel.center_x,self.genelabel.y = self.center_x,self.y-40
        genes = f"[b]{self.model.colorgenes} {self.model.heightgenes}[/b]"
        if self.model.pollinator:
            p = self.model.pollinator
            self.genelabel.text = f"plant: {genes}\npollen: [b]{p.colorgenes} {p.heightgenes}[/b]\n{self.model.id}"
        else:
            self.genelabel.text = f"{genes}\n{self.model.id}\n"

        cx = self.x+self.width/2
        cy = self.y+self.height/2
        if self.model.age < 10:
            self.canvasthing.add(Color(.4,.25,.1,1))
            self.canvasthing.add(Ellipse(pos=(cx-8,cy-5),size=(16,10)))
        elif self.model.age < 20:
            self.canvasthing.add(Color(.2,.7,.2,1))
            self.canvasthing.add(Line(points=[cx,cy-10,cx,cy+20],width=2))
            self.canvasthing.add(Ellipse(pos=(cx-14,cy+5),size=(14,7)))
            self.canvasthing.add(Ellipse(pos=(cx,cy+8),size=(14,7)))
        else:
            h = 50*self.model.phenoheight
            self.canvasthing.add(Color(.1,.4,.1,1))
            self.canvasthing.add(Rectangle(pos=(cx-2,cy-10),size=(4,h)))
            self.canvasthing.add(Color(.1,.6,.1,1))
            self.canvasthing.add(Ellipse(pos=(cx-25,cy+10),size=(25,12)))
            self.canvasthing.add(Ellipse(pos=(cx+2,cy+20),size=(25,12)))
            if self.model.age >= 30:
                if self.model.pollinator:
                    self.canvasthing.add(Color(1,.9,0,.2))
                    self.canvasthing.add(Ellipse(pos=(cx-30,cy+h-25),size=(60,60)))
                self.canvasthing.add(Color(*self.model.phenocolor))
                for i in range(0,360,72):
                    rad = math.radians(i)
                    self.canvasthing.add(Ellipse(pos=(cx+18*math.cos(rad)-11,cy+h+18*math.sin(rad)-11),size=(22,22)))
                self.canvasthing.add(Ellipse(pos=(cx-11,cy+h-11),size=(22,22)))
                self.canvasthing.add(Color(.9,.8,0,1))
                self.canvasthing.add(Ellipse(pos=(cx-9,cy+h-9),size=(18,18)))

    def on_touch_down(self,touch):
        if self.collide_point(*touch.pos):
            if not self.model.planted or self.model.harvestable:
                self.parent.freeplot(self)
                self.model.planted = False
                touch.grab(self)
                return True
        return super().on_touch_down(touch)

    def on_touch_move(self,touch):
        if touch.grab_current is self:
            self.pos = (touch.x-self.width/2,touch.y-self.height/2)
            return True

    def on_touch_up(self,touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.parent.handledrop(self)
            return True
        return super().on_touch_up(touch)

class tnode(Widget):
    def __init__(self,model,**kwargs):
        super().__init__(**kwargs)
        self.size = (110,60)
        self.size_hint = (None,None)
        self.model = model
        with self.canvas.before:
            Color(.12,.12,.12,1)
            RoundedRectangle(pos=self.pos,size=self.size,radius=[4])
            Color(.3,.3,.3,1)
            Line(rounded_rectangle=(self.x,self.y,self.width,self.height,4),width=1.5)
            Color(*model.phenocolor)
            if model.phenoheight == 1.4:
                Ellipse(pos=(self.x+8,self.y+self.height-16),size=(8,8))
            else:
                Rectangle(pos=(self.x+8,self.y+self.height-16),size=(8,8))

        genes = f"[b]{model.colorgenes}[/b] | {model.heightgenes}\n[size=10sp]ID: {model.id}[/size]"
        self.label = Label(text=genes,markup=True,pos=self.pos,size=self.size,halign="center",valign="middle",font_size="13sp")
        self.label.bind(size=self.label.setter('text_size'))
        self.add_widget(self.label)
        self.bind(pos=self.update,size=self.update)

    def update(self,*args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(.15,.15,.15,1)
            RoundedRectangle(pos=self.pos,size=self.size,radius=[4])
            Color(.4,.4,.4,1)
            Line(rounded_rectangle=(self.x,self.y,self.width,self.height,4),width=1.2)
            Color(*self.model.phenocolor)
            Rectangle(pos=(self.x+8,self.y+self.height-16),size=(8,8))
        self.label.pos = self.pos

class treeclass(FloatLayout):
    def __init__(self,history,**kwargs):
        super().__init__(**kwargs)
        self.history = history
        self.testidx = 0
        self.npos = {}

        self.scatter = Scatter(do_rotation=False,do_scale=True,auto_bring_to_front=False,size_hint=(None,None),size=(40000,40000))
        with self.scatter.canvas.before:
            Color(.05,.1,.05,.95)
            Rectangle(pos=(0,0),size=(40000,40000))
        self.add_widget(self.scatter)

        self.layout = GridLayout(rows=1,size_hint=(None,None),height=50,spacing=10)
        self.add_widget(self.layout)

        self.bind(size=self.update)
        self.refresh()

    def update(self,*args):
        self.layout.top = self.height-20
        self.layout.x = 20
        self.scatter.pos = (self.width/2-20000,self.height/2-20000)

    def switch(self,index):
        self.testidx = index
        self.refresh()

    def refresh(self):
        self.scatter.clear_widgets()
        self.scatter.canvas.clear()
        self.layout.clear_widgets()
        with self.scatter.canvas.before:
            Color(.05,.1,.05,.95)
            Rectangle(pos=(0,0),size=(40000,40000))

        if not self.history:
            return
        tests = sorted(list(set(i.test for i in self.history.values() if i.test is not None)))
        if not tests:
            self.scatter.add_widget(Label(text="crush some plants to start a test",center=(20000,20000),font_size="20sp"))
            return
        self.testidx = min(self.testidx,len(tests)-1)
        test = tests[self.testidx]

        for i,v in enumerate(tests):
            btn = Button(text=f"test {v}",size_hint_x=None,width=120,background_color=(.2,.8,.2,1) if i == self.testidx else (.5,.5,.5,1),bold=True)
            btn.bind(on_release=lambda instance,idx=i: self.switch(idx))
            self.layout.add_widget(btn)

        filtered = set()
        for id,model in self.history.items():
            if model.test == test:
                filtered.add(id)
                if model.parents:
                    filtered.add(model.parents[0])
                    filtered.add(model.parents[1])

        depths = {}
        def getdepth(nodeid):
            if nodeid in depths:
                return depths[nodeid]
            model = self.history.get(nodeid)
            if not model or not model.parents:
                depths[nodeid] = 0
                return 0
            validparents = [p for p in model.parents if p in filtered]
            if not validparents:
                depths[nodeid] = 0
            else:
                depths[nodeid] = 1 + max(getdepth(p) for p in validparents)
            return depths[nodeid]
        for nodeid in filtered:
            getdepth(nodeid)

        XSTEP = 160
        YSTEP = 160
        ROOTX = 20000
        ROOTY = 20000

        levels = {}
        for id in filtered:
            d = depths.get(id,0)
            levels.setdefault(d,[]).append(id)
        self.npos = {}

        for d in sorted(levels.keys()):
            ids = levels[d]
            groups = {}
            for id in ids:
                model = self.history[id]
                groups.setdefault(tuple(sorted(model.parents)) if model.parents else ("root",id),[]).append(id)

            ideals = {}
            for p,members in groups.items():
                if p[0] == "root":
                    ideals[p] = ROOTX
                else:
                    p1,p2 = p
                    if p1 in self.npos and p2 in self.npos:
                        ideals[p] = (self.npos[p1][0]+self.npos[p2][0])/2
                    else:
                        ideals[p] = ROOTX

            currentx = 0
            offsets = {}
            for idx,p in enumerate(sorted(groups.keys(),key=lambda k: ideals[k])):
                members = groups[p]
                if idx > 0:
                    currentx += XSTEP*.6
                for member in members:
                    offsets[member] = currentx
                    currentx += XSTEP

            if offsets:
                totalwidth = currentx-XSTEP
                startx = ROOTX-(totalwidth/2)
                for id,offset in offsets.items():
                    y = ROOTY-(d*YSTEP)
                    x = startx+offset
                    node = tnode(self.history[id],pos=(x,y))
                    self.npos[id] = (x+55,y)
                    self.scatter.add_widget(node)

        # this is a miracle that was bestowed to me by god himself (real) (it took SO LONG)
        with self.scatter.canvas.before:
            Color(.7,.7,.7,1)
            for id in filtered:
                model = self.history.get(id)
                if model and model.parents:
                    p1,p2 = model.parents
                    if p1 in self.npos and p2 in self.npos and id in self.npos:
                        p1x,p1y = self.npos[p1]
                        p2x,p2y = self.npos[p2]
                        cx,cy = self.npos[id]
                        topedge = cy+60
                        marriagey = min(p1y,p2y)-35
                        Line(points=[p1x,p1y,p1x,marriagey],width=1.5)
                        Line(points=[p2x,p2y,p2x,marriagey],width=1.5)
                        Line(points=[p1x,marriagey,p2x,marriagey],width=1.5)
                        marriagex = (p1x+p2x)/2
                        splity = (marriagey+topedge)/2
                        Line(points=[marriagex,marriagey,marriagex,splity,cx,splity,cx,topedge],width=1.5)

class game(FloatLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.history = {}
        w,h = self.width,self.height
        self.unit = h*.08

        self.infolabel = Label(text="[b]GUIDE:[/b]\nR = red  |  r = white\nT = tall  |  t = short\n\n[b]INSTRUCTIONS:[/b]\n1. Drag seeds to brown plots\n2. Wait for them to grow into flowers\n3. Touch flowers together to pollinate\n4. Drag pollinated plant to the nefarious [b]CRUSHER OF AGONY AND DESPAIR[/b] (right there)\n\n",markup=True,size_hint=(None,None),halign="left")
        self.infolabel.bind(texture_size=self.infolabel.setter('size'))

        self.loglabel = Label(text="\n\n[b]CRUSHER OF AGONY AND DESPAIR --->[/b]\nCrush a pollinated plant\nto see genetic odds",markup=True,size_hint=(None,None),halign="right")
        self.loglabel.bind(texture_size=self.loglabel.setter('size'))

        self.plots = []
        self.plotoccupants = [None]*8
        self.bind(size=self.update,pos=self.update)
        with self.canvas.before:
            Color(0,.2,0,1)
            self.bg = Rectangle(size=self.size,pos=self.pos)
            Color(.4,.3,.2,1)
            for i in range(8):
                r = Rectangle()
                self.plots.append(r)
        self.crusher = Widget(size_hint=(None,None))
        with self.crusher.canvas:
            Color(.5,.2,.2,1)
            self.crush = Rectangle()
        self.add_widget(self.crusher)
        self.buybtn = Button(text="SPAWN SEED",size_hint=(None,None),size=(140,50),background_color=(0,.6,1,1),bold=True)
        self.buybtn.bind(on_release=self.spawn)
        self.treeview = None
        self.treebtn = Button(text="VIEW GENE TREE",size_hint=(None,None),size=(140,50),pos=(20,Window.height-70))
        self.treebtn.bind(on_release=self.treetoggle)

        self.add_widget(self.buybtn)
        self.add_widget(self.infolabel)
        self.add_widget(self.loglabel)
        self.add_widget(self.treebtn,index=0)

    def treetoggle(self,*args):
        if self.treeview:
            self.remove_widget(self.treeview)
            self.treeview = None
            self.treebtn.text = "VIEW GENE TREE"
        else:
            self.treeview = treeclass(self.history,size_hint=(1,1),pos=(0,0))
            self.add_widget(self.treeview,index=1)
            self.treebtn.text = "CLOSE TREE"

    def update(self,*args):
        self.bg.size = self.size
        self.bg.pos = self.pos
        w,h = self.width,self.height
        self.unit = h*.08
        plotsize = self.unit*1.2
        spacing = self.unit*.5
        y = (h-(plotsize*4+spacing*4))*.9
        plotx = w*.05
        plotx2 = plotx+plotsize+spacing
        for i,rect in enumerate(self.plots):
            rowx = plotx if i < 4 else plotx2
            rect.size = (plotsize,plotsize)
            rect.pos = (rowx,y+i%4*(plotsize+spacing))

        crushsize = self.unit*2
        self.crusher.size = (crushsize,crushsize)
        self.crusher.pos = (w-crushsize-self.unit*.4,h-crushsize-self.unit*.4)
        self.crush.pos = self.crusher.pos
        self.crush.size = self.crusher.size

        self.buybtn.size = (self.unit*3.5,self.unit*.9)
        self.buybtn.font_size = f"{self.unit*.22}sp"
        self.buybtn.pos = (w-self.buybtn.width-self.unit*.3,self.unit*.3)
        self.treebtn.size = (self.unit*3.5,self.unit*.9)
        self.treebtn.font_size = f"{self.unit*.22}sp"
        self.treebtn.pos = (w-self.buybtn.width-self.unit*.3,self.unit*1.3)
        self.infolabel.text_size = (None,None)
        self.infolabel.font_size = max(12,self.unit*.25)
        self.infolabel.texture_update()
        self.infolabel.x = w*.02
        self.infolabel.y = self.unit*.2
        self.loglabel.text_size = (None,None)
        self.loglabel.font_size = max(14,self.unit*.28)
        self.loglabel.texture_update()
        self.loglabel.right = self.crusher.x-(self.unit*.5)
        self.loglabel.top = self.crusher.top+(self.unit*.5)

        if hasattr(self,"table"):
            self.table.center = (w/2,h/2)

    def spawn(self,*args):
        c,h = random.choice(["RR","Rr","rr"]),random.choice(["TT","Tt","tt"])
        model = plantmodel(c,h,parents=None)
        self.history[model.id] = model
        pw = plantwidget(model)
        pw.center = (self.width*.7+random.randint(1,50),100+random.randint(1,50))
        self.add_widget(pw,index=2)

    def freeplot(self,plant):
        for i,occupant in enumerate(self.plotoccupants):
            if occupant == plant:
                self.plotoccupants[i] = None

    def handledrop(self,plant):
        if self.crusher.collide_widget(plant):
            if plant.model.pollinator:
                self.breed(plant.model,plant.model.pollinator)
            self.remove_widget(plant)
            return
        if plant.model.harvestable:
            for i in self.children:
                if isinstance(i,plantwidget) and i != plant and i.model.harvestable:
                    if plant.collide_widget(i):
                        plant.model.pollinator = i.model
                        i.model.pollinator = plant.model
                        plant.update(0)
                        i.update(0)
                        return

        for i,v in enumerate(self.plots):
            rx,ry = v.pos
            rw,rh = v.size
            px,py = plant.center
            if rx <= px <= rx+rw and ry <= py <= ry+rh:
                if self.plotoccupants[i] is None and not plant.model.harvestable:
                    plant.center = (rx+rw/2,ry+rh/2)
                    plant.model.planted = True
                    self.plotoccupants[i] = plant
                    return

    def getgametes(self,model):
        gametes = []
        for c in model.colorgenes:
            for h in model.heightgenes:
                gametes.append(c+h)
        return gametes,model.colorgenes+model.heightgenes

    def tableupdate(self,m1,m2,genotypes):
        self.unit2 = self.unit/2
        grid = GridLayout(cols=5,spacing=self.unit/10,size_hint=(None,None))
        grid.bind(minimum_size=grid.setter("size"))

        g1,t1 = self.getgametes(m1)
        g2,t2 = self.getgametes(m2)
        colormap = {}
        for i,geno in enumerate(genotypes):
            colormap[geno] = RCOLORS[i%len(RCOLORS)]
        grid.add_widget(Label(text="",size_hint_y=None,height=self.unit2))
        for gamete in g2:
            grid.add_widget(Label(text=gamete,bold=True,color=(.7,.7,.7,1),size_hint_y=None,height=self.unit2))
        cells = 16
        counts = {geno: 0 for geno in genotypes}

        for r in g1:
            grid.add_widget(Label(text=r,bold=True,color=(.7,.7,.7,1),size_hint_x=None,width=self.unit2*2))
            for i in g2:
                c = "".join(sorted(r[0]+i[0]))
                h = "".join(sorted(r[1]+i[1]))
                cellgeno = c+h
                if cellgeno in counts:
                    counts[cellgeno] += 1
                    cellcolor = colormap[cellgeno]['rgba']
                else:
                    cellcolor = (1,1,1,1)
                label = Label(text=cellgeno,color=cellcolor,bold=(cellgeno in counts),size_hint=(None,None),size=(self.unit2*2,self.unit2))
                grid.add_widget(label)

        log = f"[b]{t1}[/b] x [b]{t2}[/b]\n"
        for geno in genotypes:
            percent = (counts[geno]/cells)*100
            log += f"[color=#{colormap[geno]['hex']}][b]{geno}[/b][/color] spawned | chance: {percent:.1f}%\n"
        self.loglabel.text = log.strip()

        if hasattr(self,"table"):
            Animation.stop_all(self.table)
            self.remove_widget(self.table)

        self.table = Scatter(size_hint=(None,None),do_rotation=False,do_translation=False,do_scale=False,opacity=1)
        self.table.add_widget(grid)
        self.add_widget(self.table,index=len(self.children))

        def finalize(dt):
            self.table.size = grid.size
            self.table.center = (self.width/2,self.height/2)
        Clock.schedule_once(finalize)

        def fade(dt):
            anim = Animation(opacity=0,duration=3)
            anim.bind(on_complete=lambda *x: self.remove_widget(self.table) if hasattr(self,"table") else None)
            anim.start(self.table)
        Clock.schedule_once(fade,6)

    def breed(self,m1,m2):
        if m1.test is not None:
            test = m1.test
        elif m2.test is not None:
            test = m2.test
        else:
            plantmodel.counter += 1
            test = plantmodel.counter
        m1.test = test
        m2.test = test

        n = min(1,math.floor(math.sqrt(random.randint(1,19)/2)))
        spawned = []
        for z in range(n):
            newc = crossover(m1.colorgenes,m2.colorgenes)
            newh = crossover(m1.heightgenes,m2.heightgenes)
            child = plantmodel(newc,newh,parents=(m1.id,m2.id),test=test)
            self.history[child.id] = child
            spawned.append(child)
            widget = plantwidget(child)
            widget.center = (self.crusher.center_x+random.randint(-50,50),self.crusher.y-80+random.randint(-40,40))
            self.add_widget(widget,index=2)
        uniquelist = list(set([i.colorgenes+i.heightgenes for i in spawned]))
        self.tableupdate(m1,m2,uniquelist)

class app(App):
    def build(self):
        return game()

if __name__ == "__main__":
    app().run()
