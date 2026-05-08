import random
import math
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color,Ellipse,Rectangle,InstructionGroup,Line
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.core.window import Window

def crossover(p1,p2):
    return "".join(sorted(random.choice(p1)+random.choice(p2)))

class plantmodel:
    def __init__(self,color_genes="Rr",height_genes="Tt"):
        self.color_genes = "".join(sorted(color_genes))
        self.height_genes = "".join(sorted(height_genes))
        self.age = 0
        self.is_planted = False
        self.is_harvestable = False
        self.pollinated_by = None

    @property
    def phenotype_color(self):
        return (.9,.1,.1,1) if "R" in self.color_genes else (1,1,1,1)

    @property
    def phenotype_height(self):
        return 1.4 if "T" in self.height_genes else .8

    def update(self,dt):
        if self.is_planted and self.age < 30:
            self.age += dt*2
            if self.age >= 30:
                self.is_harvestable = True

class plantwidget(Widget):
    def __init__(self,model,**kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.size = (80,80)
        self.size_hint = (None,None)

        self.gene_label = Label(text=f"{self.model.color_genes}\n{self.model.height_genes}",
                                color=(1,1,1,.7),font_size="10sp",bold=True,halign="center")
        self.add_widget(self.gene_label)

        self.canvas_group = InstructionGroup()
        self.canvas.add(self.canvas_group)
        Clock.schedule_interval(self.update_view,1/30)

    def update_view(self,dt):
        self.model.update(dt)
        self.canvas_group.clear()
        self.gene_label.center_x,self.gene_label.y = self.center_x,self.y-25
        genes = f"{self.model.color_genes} {self.model.height_genes}"
        if self.model.pollinated_by:
            p = self.model.pollinated_by
            self.gene_label.text = f"plant: {genes}\npollen: {p.color_genes} {p.height_genes}"
        else:
            self.gene_label.text = genes

        cx = self.x+self.width/2
        cy = self.y+self.height/2
        h_mult = self.model.phenotype_height

        if self.model.age < 10:
            self.canvas_group.add(Color(.4,.25,.1,1))
            self.canvas_group.add(Ellipse(pos=(cx-8,cy-5),size=(16,10)))

        elif self.model.age < 20:
            self.canvas_group.add(Color(.2,.7,.2,1))
            self.canvas_group.add(Line(points=[cx,cy-10,cx,cy+20],width=2))
            self.canvas_group.add(Ellipse(pos=(cx-14,cy+5),size=(14,7)))
            self.canvas_group.add(Ellipse(pos=(cx,cy+8),size=(14,7)))

        else:
            h = 50*h_mult
            self.canvas_group.add(Color(.1,.4,.1,1))
            self.canvas_group.add(Rectangle(pos=(cx-2,cy-10),size=(4,h)))
            self.canvas_group.add(Color(.1,.6,.1,1))
            self.canvas_group.add(Ellipse(pos=(cx-25,cy+10),size=(25,12)))
            self.canvas_group.add(Ellipse(pos=(cx+2,cy+20),size=(25,12)))

            if self.model.age >= 30:
                if self.model.pollinated_by:
                    self.canvas_group.add(Color(1,.9,0,.2))
                    self.canvas_group.add(Ellipse(pos=(cx-30,cy+h-25),size=(60,60)))
                self.canvas_group.add(Color(*self.model.phenotype_color))
                for a in range(0,360,72):
                    rad = math.radians(a)
                    self.canvas_group.add(Ellipse(pos=(cx+18*math.cos(rad)-11,cy+h+18*math.sin(rad)-11),size=(22,22)))
                self.canvas_group.add(Ellipse(pos=(cx-11,cy+h-11),size=(22,22)))
                self.canvas_group.add(Color(.9,.8,0,1))
                self.canvas_group.add(Ellipse(pos=(cx-9,cy+h-9),size=(18,18)))

    def on_touch_down(self,touch):
        if self.collide_point(*touch.pos):
            if not self.model.is_planted or self.model.is_harvestable:
                self.parent.free_plot_by_plant(self)
                self.model.is_planted = False
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
            self.parent.handle_drop(self)
            return True
        return super().on_touch_up(touch)

class game(FloatLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

        self.info_label = Label(
            text="[b]GUIDE:[/b]\nR = red  |  r = white\nT = tall  |  t = short\n\n[b]INSTRUCTIONS:[/b]\n1. Drag seeds to brown plots\n2. Wait for them to grow into flowers\n3. Touch flowers together to pollinate\n4. Drag pollinated plant to the nefarious [b]CRUSHER OF AGONY AND DESPAIR[/b] (right there)",
            markup=True,size_hint=(None,None),size=(300,200),
            pos=(150,10),halign="left",font_size="13sp"
        )
        self.add_widget(self.info_label)

        self.log_label = Label(
            text="[b]CRUSHER OF AGONY AND DESPAIR --->[/b]\nCrush a pollinated plant\nto see genetic odds",
            markup=True,size_hint=(None,None),size=(250,100),
            halign="center",color=(.8,.8,.8,1)
        )
        self.add_widget(self.log_label)

        self.plot_rects = []
        self.plot_occupants = [None]*4

        self.bind(size=self._update_ui,pos=self._update_ui)

        with self.canvas.before:
            Color(0,.2,0,1)
            self.bg = Rectangle(size=self.size,pos=self.pos)
            Color(.4,.3,.2,1)
            for i in range(4):
                r = Rectangle()
                self.plot_rects.append(r)
        self.crusher = Widget(size_hint=(None,None))
        with self.crusher.canvas:
            Color(.5,.2,.2,1)
            self.crush_rect = Rectangle()
        self.add_widget(self.crusher)
        #self.crush_label = Label(text="SEED\nCRUSHER",bold=True,halign="center",font_size="12sp")
        #self.add_widget(self.crush_label)
        self.buy_btn = Button(text="SPAWN SEED",size_hint=(None,None),size=(140,50),background_color=(0,.6,1,1),bold=True)
        self.buy_btn.bind(on_release=self.spawn_initial)
        self.add_widget(self.buy_btn)

    def _update_ui(self,*args):
        self.bg.size,self.bg.pos = self.size,self.pos
        self.unit = min(self.width,self.height)/10

        plot_sz = self.unit*1.1
        padding = 25
        start_y = (self.height-(4*plot_sz+3*padding))/1.3
        for i,rect in enumerate(self.plot_rects):
            rect.size = (plot_sz,plot_sz)
            rect.pos = (50,start_y+i*(plot_sz+padding))

        crush_sz = self.unit*1.8
        self.crusher.size = (crush_sz,crush_sz)
        self.crusher.pos = (self.width-crush_sz-30,self.height-crush_sz-30)

        self.crush_rect.pos = self.crusher.pos
        self.crush_rect.size = self.crusher.size
        #self.crush_label.center_x = self.crusher.center_x
        #self.crush_label.top = self.crusher.center_y-100

        self.buy_btn.pos = (self.width-self.buy_btn.width-20,20)
        self.info_label.pos = (150,10)
        self.log_label.center_x = self.crusher.x-200
        self.log_label.center_y = self.crusher.center_y

        if hasattr(self,"table_container"):
            self.table_container.center_x = self.log_label.center_x-60
            self.table_container.top = self.log_label.y-60

    def spawn_initial(self,*args):
        c,h = random.choice(["RR","Rr","rr"]),random.choice(["TT","Tt","tt"])
        pw = plantwidget(plantmodel(c,h))
        pw.center = (self.width*.7+random.randint(1,50),100+random.randint(1,50))
        self.add_widget(pw)

    def free_plot_by_plant(self,plant):
        for i,occupant in enumerate(self.plot_occupants):
            if occupant == plant:
                self.plot_occupants[i] = None

    def handle_drop(self,plant):
        if self.crusher.collide_widget(plant):
            if plant.model.pollinated_by:
                self.breed_new_seed(plant.model,plant.model.pollinated_by)
                self.remove_widget(plant)
            return
        if plant.model.is_harvestable:
            for child in self.children:
                if isinstance(child,plantwidget) and child != plant and child.model.is_harvestable:
                    if plant.collide_widget(child):
                        plant.model.pollinated_by = child.model
                        child.model.pollinated_by = plant.model
                        plant.update_view(0)
                        child.update_view(0)
                        return

        for i,rect in enumerate(self.plot_rects):
            rx,ry = rect.pos
            rw,rh = rect.size
            px,py = plant.center
            if rx <= px <= rx+rw and ry <= py <= ry+rh:
                if self.plot_occupants[i] is None and not plant.model.is_harvestable:
                    plant.center = (rx+rw/2,ry+rh/2)
                    plant.model.is_planted = True
                    self.plot_occupants[i] = plant
                    return

    def get_gametes(self,model):
        gametes = []
        for c in model.color_genes:
            for h in model.height_genes:
                gametes.append(c+h)
        return gametes,model.color_genes+model.height_genes

    def update_punnett_table(self,m1,m2,result_geno):
        self.log_label.text = ""
        grid = GridLayout(cols=5,spacing=2,size_hint=(None,None))
        grid.bind(minimum_size=grid.setter("size"))
        g1,t1 = self.get_gametes(m1)
        g2,t2 = self.get_gametes(m2)
        grid.add_widget(Label(text="",size_hint_y=None,height=30))
        for gamete in g2:
            grid.add_widget(Label(text=gamete,bold=True,color=(0,.8,1,1),size_hint_y=None,height=30))
        total_cells = 16
        matches = 0
        for row_gamete in g1:
            grid.add_widget(Label(text=row_gamete,bold=True,color=(0,.8,1,1),size_hint_x=None,width=40))
            for col_gamete in g2:
                c = "".join(sorted(row_gamete[0]+col_gamete[0]))
                h = "".join(sorted(row_gamete[1]+col_gamete[1]))
                cell_geno = c+h
                is_match = (cell_geno == result_geno)
                if is_match: matches += 1
                lbl = Label(
                    text=cell_geno,
                    color=(0,1,0,1) if is_match else (1,1,1,1),
                    font_size="10sp",
                    size_hint=(None,None),size=(50,30)
                )
                grid.add_widget(lbl)
        percent = (matches/total_cells)*100
        self.log_label.text = f"{t1} + {t2}\n[b]Result: {result_geno}[/b]\nChance: {percent:.1f}%"
        if hasattr(self,"table_container"): self.remove_widget(self.table_container)
        self.table_container = grid
        self.table_container.center_x = self.log_label.center_x-60
        self.table_container.top = self.log_label.y-60
        self.add_widget(self.table_container)

    def breed_new_seed(self,m1,m2):
        new_c = crossover(m1.color_genes,m2.color_genes)
        new_h = crossover(m1.height_genes,m2.height_genes)
        result_genotype = new_c+new_h
        self.update_punnett_table(m1,m2,result_genotype)
        child = plantwidget(plantmodel(new_c,new_h))
        child.center = (self.crusher.center_x+random.randint(1,50),self.crusher.y-250+random.randint(1,50))
        self.add_widget(child)

class app(App):
    def build(self):
        return game()

if __name__ == "__main__":
    app().run()
