#!/usr/bin/python

import random
import sys
import getopt
import logging
from PIL import Image, ImageDraw, ImageFont
from math import sqrt

def rand_seq(size):
    '''generates values in random order
    equivalent to using shuffle in random,
    without generating all values at once'''
    values=range(size)
    for i in xrange(size):
        # pick a random index into remaining values
        j=i+int(random.random()*(size-i))
        # swap the values
        values[j],values[i]=values[i],values[j]
        # return the swapped value
        yield values[i] 

def all_pairs(size):
    '''generates all i,j pairs for i,j from 0-size'''
    for i in rand_seq(size):
        for j in rand_seq(size):
            yield (i,j)

def reversed_sections(tour):
    '''generator to return all possible variations where the section between two cities are swapped'''
    for i,j in all_pairs(len(tour)):
        if i != j:
            copy=tour[:]
            if i < j:
                copy[i:j+1]=reversed(tour[i:j+1])
            else:
                copy[i+1:]=reversed(tour[:j])
                copy[:j]=reversed(tour[i+1:])
            if copy != tour: # no point returning the same tour
                yield copy

#def swapped_cities(tour):
#    '''generator to create all possible variations where two cities have been swapped'''
#    for i,j in all_pairs(len(tour)):
#        if i < j:
#            copy=tour[:]
#            copy[i],copy[j]=tour[j],tour[i]
#            yield copy

def cartesian_matrix(coords):
    '''create a distance matrix for the city coords that uses straight line distance'''
    matrix={}
    for i,(x1,y1) in enumerate(coords):
        for j,(x2,y2) in enumerate(coords):
            dx,dy=x1-x2,y1-y2
            dist=sqrt(dx*dx + dy*dy)
            matrix[i,j]=dist
    return matrix

def read_coords(coord_file):
    '''
    read the coordinates from file and return the distance matrix.
    coords should be stored as comma separated floats, one x,y pair per line.
    '''
    coords=[]
    for line in coord_file:
        x,y=line.strip().split(',')
        coords.append((float(x),float(y)))
    return coords

def calculate_tour_length(matrix,tour):
    '''total up the total length of the tour based on the distance matrix'''
    total=0
    num_cities=len(tour)
    for i in range(num_cities):
        j=(i+1)%num_cities
        city_i=tour[i]
        city_j=tour[j]
        total+=matrix[city_i,city_j]
    return -total

def write_tour_to_img(coords,tour,title,img_file):
    padding=20
    # shift all coords in a bit
    coords=[(x+padding,y+padding) for (x,y) in coords]
    maxx,maxy=0,0
    for x,y in coords:
        maxx=max(x,maxx)
        maxy=max(y,maxy)
    maxx+=padding
    maxy+=padding
    img=Image.new("RGB",(int(maxx),int(maxy)),color=(255,255,255))
    
    font=ImageFont.load_default()
    d=ImageDraw.Draw(img);
    num_cities=len(tour)
    for i in range(num_cities):
        j=(i+1)%num_cities
        city_i=tour[i]
        city_j=tour[j]
        x1,y1=coords[city_i]
        x2,y2=coords[city_j]
        d.line((int(x1),int(y1),int(x2),int(y2)),fill=(0,0,0))
        d.text((int(x1)+7,int(y1)-5),str(i),font=font,fill=(32,32,32))
    
    
    for x,y in coords:
        x,y=int(x),int(y)
        d.ellipse((x-5,y-5,x+5,y+5),outline=(0,0,0),fill=(196,196,196))
    
    d.text((1,1),title,font=font,fill=(0,0,0))
    
    del d
    img.save(img_file, "PNG")

def init_random_tour(num_cities):
   tour=range(num_cities)
   random.shuffle(tour)
   return tour


def hillclimb(coords,max_evaluations):
    '''
    hillclimb until either max_evaluations is reached or we are at a local optima
    '''
    random_tour=init_random_tour(len(coords))
    matrix=cartesian_matrix(coords)
    best=init_random_tour(len(coords))
    best_score=calculate_tour_length(matrix,best)
    
    num_evaluations=1
    
    logging.info('hillclimb started: score=%f',best_score)
    
    while num_evaluations < max_evaluations:
        # examine moves around our current position
        move_made=False
        for next in reversed_sections(best):
            if num_evaluations >= max_evaluations:
                break
            
            # see if this move is better than the current
            next_score=calculate_tour_length(matrix,next)
            num_evaluations+=1
            if next_score > best_score:
                best=next
                best_score=next_score
                move_made=True
                break # depth first search
            
        if not move_made:
            break # we couldn't find a better move (must be at a local maximum)
    
    logging.info('hillclimb finished: num_evaluations=%d, best_score=%f',num_evaluations,best_score)
    return (num_evaluations,best_score,best)

def hillclimb_and_restart(coords,max_evaluations):
    '''
    repeatedly hillclimb until max_evaluations is reached
    '''
    best=None
    best_score=0
    
    num_evaluations=0
    while num_evaluations < max_evaluations:
        remaining_evaluations=max_evaluations-num_evaluations
        
        logging.info('(re)starting hillclimb %d/%d remaining',remaining_evaluations,max_evaluations)
        evaluated,score,found=hillclimb(coords,remaining_evaluations)
        
        num_evaluations+=evaluated
        if score > best_score or best is None:
            best_score=score
            best=found
        
    return (num_evaluations,best_score,best)




#def run_hillclimb(coords,max_iterations):
#    from hillclimb import hillclimb_and_restart
#    iterations,score,best=hillclimb_and_restart(coords,max_iterations)
#    return iterations,score,best


def usage():
    print "usage: python %s [-o <output image file>] [-v] [-m reversed_sections|swapped_cities] -n <max iterations> [-a hillclimb|anneal] [--cooling start_temp:alpha] <city file>" % sys.argv[0]

def main():
    try:
        options, args = getopt.getopt(sys.argv[1:], "ho:vn:w:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    out_file_name=None
    max_iterations=None
    verbose=None
    #move_operator=reversed_sections
    workers=1
    #run_algorithm=run_hillclimb
    
    
    for option,arg in options:
        if option == '-v':
            verbose=True
        elif option == '-h':
            usage()
            sys.exit()
        elif option == '-o':
            out_file_name=arg
        elif option == '-n':
            max_iterations=int(arg)
        elif option == '-w':
            workers=int(arg)
    
    if max_iterations is None:
        usage();
        sys.exit(2)
    
    if out_file_name and not out_file_name.endswith(".png"):
        usage()
        print "output image file name must end in .png"
        sys.exit(1)
    
    if len(args) != 1:
        usage()
        print "no city file specified"
        sys.exit(1)
    
    city_file=args[0]
    
    # enable more verbose logging (if required) so we can see workings
    # of the algorithms
    import logging
    format='%(asctime)s %(levelname)s %(message)s'
    if verbose:
        logging.basicConfig(level=logging.INFO,format=format)
    else:
        logging.basicConfig(format=format)
    
    # setup the things tsp specific parts hillclimb needs
    coords=read_coords(file(city_file))
    #random_tour=init_random_tour(len(coords))
    #matrix=cartesian_matrix(coords)
    #tour_length=lambda tour: calculate_tour_length(matrix,tour)
    
    #logging.info('using move_operator: %s'%move_operator)
    
    iterations,score,best=hillclimb_and_restart(coords,max_iterations)
    # output results
    print iterations,-score,best
    
    if out_file_name:
        write_tour_to_img(coords,best,'%s: %f'%(city_file,score),file(out_file_name,'w'))

if __name__ == "__main__":
    main()
