import minidem as dem
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from scipy.stats import norm
import numpy as np
import random
import time

LoiN = False # Booléen faux si loi normale pas tracée et vrai si tracée
dem.simu.custom_title = True # Permet de modifier le titre de la scène
# Choix du nombre de colonnes
n_columns=int(input("Combien voulez-vous de colonnes sur la simulation ? (veuillez choisir un nombre entre 4 et 10) : "))
while n_columns<4 or n_columns>10 :
    print("Attention, il faut choisir un nombre de colonnes compris entre 4 et 10 !")
    n_columns=int(input("Combien voulez-vous de colonnes sur le simulation ? "))

# Choix du nombre d'itérations
n_iterations = int(input("Combien d'iterations voulez-vous que dure la simulation ? (pour une simulation pertinente, une valeur comprise entre 1000 et 10000 est recommandée) : "))

# Définition des limites de la scène
dem.simu.xlim=(-120,120)
dem.simu.ylim=(0,280)

# Définition des différents listes qui contiendront les éléments de la simulation
glued_balls_list =[]
moving_balls_list = []
coordinates_columns=[]
list_points_entonnoirX=[]

count=0 # Initalisation du compte de nombres de balles qui auront été simulées

#initialisation des listes contenants les rectangles et texte pour le comptage
L_rect = []
L_text = []
   
L_compte = [0]*n_columns #initialisation d'une liste contenant autant de 0 qu'il y a de colonnes (elle servira au compte des balles)

# Fonction permettant de fixer les balles qui ne sont pas censées bouger
def stick_glued_balls():
    for gr in (glued_balls_list+moving_balls_list):
        gr.pos=dem.vec(gr.initial_pos[0],gr.initial_pos[1])
        gr.vel=dem.vec(0,0)

# Fonction permettant de détecter et gérer les contacts entre les billes
def manage_contact():
    l = dem.lcm.compute_colliding_pair()
    for (gr1,gr2) in l:
        dem.contact(gr1,gr2, stiffness = 4e5, restitution_coef=0.4)

# Fonction permettant d'ajouter une force de pesanteur aux billes
def add_gravity_force():
    for gr in dem.simu.grain_list:
        gr.force += gr.mass*dem.vec(0., -60)

# Fonction permettant de limiter le mouvement des billes de haut en bas
def not_going_everywhere():
    for gr in dem.simu.grain_list:
        if gr.vel[1]>0:
            gr.vel[1]=0

def add_viscous_force():
    c = 20 # the viscous factor
    for gr in dem.simu.grain_list:
        if gr.pos[1]<200:
            gr.force += -gr.vel[0]*c
            
# Fonction permettant la détection d'un appui sur la touche espace (pour faire apparaitre des billes notamment)
def on_press(event):
    if event.key == ' ': # if the key is space, toggle the start variable
        if len(moving_balls_list) > 0:
            grain=moving_balls_list[0]
            x_pos=random.randint(-30,30)
            y_pos=240
            grain.pos=dem.vec(x_pos,y_pos)
            moving_balls_list.remove(grain)
        else :
            None

# Fonction permettant de créer des limites physiques aux balles : des murs à droite, à gauche et en haut, ainsi que les colonnes et l'entonnoir. Elle permet également le comptage des billes tombées dans chacunes des colonnes
def rigid_wall():
    global count
    f = 1. # the elastic/inelastic factor. It must be in the [0;1] range.
    for gr in dem.simu.grain_list:
        if gr not in moving_balls_list:  
            if gr.pos[0] - gr.radius < -120:
               gr.pos[0] = gr.radius-120
               if gr.vel[0] < 0.:
                  gr.vel[0] *= -f
            elif gr.pos[0] + gr.radius > 120:
               gr.pos[0] = 120 - gr.radius
               if gr.vel[0] > 0.:
                  gr.vel[0] *= -f
                 
            ### determiner le trou dans lequel la balle est tombée
            list_holes=[]
            for coord in coordinates_columns:
                list_holes.append(coord-gr.pos[0])
            dist_holes=[]
            for hole in list_holes:
                dist_holes.append(abs(hole))
                closest_hole=dist_holes.index(min(dist_holes))
            if list_holes[closest_hole]<=0:
                closest_hole+=1
               
            if gr.pos[1] - gr.radius < 0 and gr not in glued_balls_list:
               gr.pos=dem.vec(-20+2*count*radius,420)
               moving_balls_list.append(gr)
               count+=1
               L_compte[closest_hole-1]+=1
               L_text[closest_hole-1].set_text(str(L_compte[closest_hole-1]))
               L_rect[closest_hole-1].set_height(2*(L_compte[closest_hole-1]+1))
               
            ### si la balle tombe sur les côtés du rectangle
            if gr.pos[1]<=60:
                if gr.pos[0]-gr.radius<=coordinates_columns[closest_hole-1]+rad:
                    gr.pos[0]=coordinates_columns[closest_hole-1]+rad+gr.radius
                    if gr.vel[0]<0.:
                        gr.vel[0] *= -f
                if gr.pos[0]+gr.radius>=coordinates_columns[closest_hole]-rad:
                    gr.pos[0]=coordinates_columns[closest_hole]-rad-gr.radius
                    if gr.vel[0]>0.:
                        gr.vel[0] *= -f
            ###  si la balle tombe au sommet du rectangle
            if gr.pos[1]-gr.radius<=60:
                distX_left=abs(gr.pos[0]-(coordinates_columns[closest_hole-1]+rad))
                distX_right=abs(gr.pos[0]-coordinates_columns[closest_hole]+rad)
                if distX_left<=rad or distX_right<=rad:
                    gr.pos[1]=gr.radius+60
                    if gr.vel[1]<0.:
                        gr.vel[1] *= -f
                       
            if gr.pos[1]<=192 and gr.pos[1]>=180:
                if gr.pos[0]+gr.radius>=-x_crochet-rad:    ###x_crochet est négatif de base
                    gr.pos[0]=-x_crochet-rad-gr.radius
                    if gr.vel[0]>0.:
                        gr.vel[0] *= -f
                if gr.pos[0]-gr.radius<=x_crochet+rad:    ###x_crochet est négatif de base
                    gr.pos[0]=x_crochet+rad+gr.radius
                    if gr.vel[0]<0.:
                        gr.vel[0] *= -f
            #### balle contre les parois de l'entonnoir
            for coordY in range(75):
                if abs(192+coordY-gr.pos[1])<=1:
                    if gr.pos[0]+gr.radius>=-x_crochet-rad+coordY:
                        gr.pos[0]=-x_crochet-rad+coordY-gr.radius
                        if gr.vel[0]>0.:
                            gr.vel[0] *= -f
                    if gr.pos[0]-gr.radius<=x_crochet+rad-coordY:
                        gr.pos[0]=x_crochet+rad-coordY+gr.radius
                        if gr.vel[0]<0.:
                            gr.vel[0] *= -f
                               
           

# Fonction qui permet une réinitialisation des forces appliquées aux billes
def reset_force():
    for gr in dem.simu.grain_list:
        gr.force = dem.vec(0., 0.)
   
# Fonction permettant l'application du PFD aux billes
def velocity_verlet():
    dt = dem.simu.dt
    for gr in dem.simu.grain_list:
        a = gr.force/gr.mass
        gr.vel += (gr.acc + a) * (dt/2.)
        gr.pos += gr.vel * dt + 0.5*a*(dt**2.)
        gr.acc  = a

# Fonction qui traçera l'histogramme et la loi normale théorique correspondants à la simulation à la fin de cette dernière
def LoiNormale():
    global LoiN
    LoiN = True

    # Création d'une liste qui permettra de créer l'histogramme
    data = []
    for i, j in enumerate(L_compte):
        for k in range(j*2):
            if i-(n_columns/2)<0:
                data.append(i-(n_columns/2))
            else :
                data.append(i-(n_columns/2))

   
    # Initalisation d'une nouvelle feuille matplotlib
    plt.figure()  

    # Tracé de l'histogramme
    plt.hist(data, bins=n_columns, density=True, alpha=0.6, color='orange', hatch = '/', align = 'right')

    # Définition des différentes valeurs permettant le tracé de la loi normale
    Valeur_Moyenne = 0
    Ecart_Type = np.std(data)
    xmin, xmax = plt.xlim()
    Nombre_Elements = np.linspace(min(data), max(data)+1, count)
    pdf = norm.pdf(Nombre_Elements, Valeur_Moyenne, Ecart_Type)

    # Tracé de la loi normale
    plt.plot(Nombre_Elements, pdf, c='r', linewidth=2, label="Courbe Gaussienne théorique")

    # Affichage de la fenêtre
    title = "Courbe gaussienne théorique en comparaison avec l'histogramme obtenu"
    plt.title(title)
    plt.show()


# the full time loop
def time_loop():
    reset_force()
    rigid_wall()
    add_gravity_force()
    add_viscous_force()
    manage_contact()
    stick_glued_balls()
    velocity_verlet()
    not_going_everywhere()
    dem.simu.print("Nombre de balles disponibles : ", len(moving_balls_list),"\nTemps écoulé : ", dem.simu.current_iter_number,"/",n_iterations)
    if (dem.simu.current_iter_number >= n_iterations ) and (LoiN == False) :
         LoiNormale()

   
# the entry point of the program
if __name__ == "__main__":                
    rad        = 1.5
    density    = 1

    #hauteur des balles fixes
    y0_columns=rad
   
    # Création des colonnes
    for x in range(int(n_columns/2+1)):
        if n_columns%2==0:
            x0_columns=int(x*225/n_columns)
        else:
            x0_columns=int(225/(2*n_columns)+225*x/n_columns)
        if x<int(n_columns/2):
            rectangle_compte = patches.Rectangle((x0_columns, 0), int(225/n_columns), 2, color="blue", alpha=0.5)
            dem.simu.add_object_to_scene(rectangle_compte)
            L_rect.append(rectangle_compte)
            texte = dem.simu.ax.text(x0_columns+int(225/(2*n_columns)), 5, "0", transform=dem.simu.ax.transData, ha="center")
            dem.simu.add_object_to_scene(texte)
            L_text.append(texte)
        rectangle = patches.Rectangle((x0_columns-rad , 0), 2*rad, 61.5, color="black", alpha=.5)
        coordinates_columns.append(x0_columns)
        dem.simu.add_object_to_scene(rectangle)
        if x0_columns!=0:
            rectangle_compte = patches.Rectangle((-x0_columns, 0), int(225/n_columns), 2, color="blue", alpha=0.5)
            dem.simu.add_object_to_scene(rectangle_compte)
            L_rect.insert(0,rectangle_compte)
            rectangle = patches.Rectangle((-x0_columns-rad , 0), 2*rad, 61.5, color="black", alpha=.5)
            coordinates_columns.append(-x0_columns)
            dem.simu.add_object_to_scene(rectangle)
            texte = dem.simu.ax.text(-x0_columns+int(225/(2*n_columns)), 5, "0", transform=dem.simu.ax.transData, ha="center")
            dem.simu.add_object_to_scene(texte)
            L_text.insert(0,texte)
    y0_columns=61.5
   
    radius=225/(4*n_columns)
    # Création de la grille de clous
    for etage in range(n_columns+1):
        y0_columns+=radius*1.5
        if n_columns%2==0:
            x0_columns=0
            if etage%2==0:
                x0_columns=int(225/(2*n_columns))
            number_of_nails=n_columns/2
        else:
            x0_columns=int(225/(2*n_columns))
            if etage%2==0:
                x0_columns=0
            number_of_nails=(n_columns+1)/2
        for bille in range(int(number_of_nails)):
                gr=dem.grain(dem.vec(x0_columns,y0_columns),rad,density,color="black")
                glued_balls_list.append(gr)
                if x0_columns!=0:
                    gr=dem.grain(dem.vec(-x0_columns,y0_columns),rad,density,color="black")
                    glued_balls_list.append(gr)
                x0_columns+=int(225/n_columns)
           
    # Initalisation de la réserve de balles
    x0_moving_balls=0
    for ball in range(50):
        x0_moving_balls+=2*radius
        y0_moving_balls=420
        gr=dem.grain(dem.vec(x0_moving_balls,y0_moving_balls),radius,density)
        moving_balls_list.append(gr)

    # Création de l'entonnoir
    x_crochet=int(-225/(2*1.25*n_columns))
    rectangle=patches.Rectangle((x_crochet - rad, 180), 2*rad, 12, color="black", alpha=.5)   # Crochet de gauche
    dem.simu.add_object_to_scene(rectangle)
    rectangle=patches.Rectangle((-x_crochet - rad , 180), 2*rad, 12, color="black", alpha=.5)   # Crochet de droite
    dem.simu.add_object_to_scene(rectangle)

    rectangle=patches.Rectangle((x_crochet - rad, 190), 2*rad, 80, angle=45.0, color="black", alpha=.5)   # Crochet de gauche
    dem.simu.add_object_to_scene(rectangle)
    rectangle=patches.Rectangle((-x_crochet - rad, 192), 2*rad, 80, angle=-45.0, color="black", alpha=.5)   # Crochet de gauche
    dem.simu.add_object_to_scene(rectangle)
    for point_X in range(75):
        list_points_entonnoirX.append(point_X+x_crochet-rad)
        list_points_entonnoirX.append(-point_X-x_crochet-rad)
    list_points_entonnoirX.sort()
   
    # Détection d'un appui sur le clavier
    coordinates_columns.sort()
    dem.simu.fig.canvas.mpl_connect('key_press_event', on_press)

   
    dem.simu.dt = 0.004 # Définition du pas de temps
    dem.run(tot_iter_number=n_iterations, update_plot_each=10, loop_fn=time_loop) # Lancement de la simulation
