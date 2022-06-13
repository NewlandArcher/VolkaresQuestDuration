import os, sys
import pprint
import copy
import random
import time
import queue
import threading

# This is an effort to see how many turns I can count on having in the Volkare's Quest scenario of
#	https://boardgamegeek.com/boardgameexpansion/130704/mage-knight-board-game-lost-legion-expansion

NUM_WOUNDS = 28

# Value in terms of movement of the cards in Volkare's deck.
#	The map is from value to the number of cards that contain that value.
MOVEMENT_VALUE_MAP = {
	0 : NUM_WOUNDS + 5,			#< wounds + 5 red cards (4 cards, 1 spell).
	1 : 12,
	2 : 3
}

TARGET_DISTANCE = 16 			#< 15 hexes and then passing through the portal on #16.

NUM_TIMES_TO_EXECUTE = 100000

class ListScrambleWorker( threading.Thread ):
	'''Class that performs the work of scrambling a list, then pushes that list onto a Queue.
	'''
	def __init__( self, queue, ordered_list ):
		threading.Thread.__init__(self)
		self.queue = queue
		self.ordered_list = ordered_list

	def run( self ):
		scrambled_movement_value_list = copy.copy( self.ordered_list )

		# Do a very basic scramble: for every index of the array, perform a swap of that index and a random index.
		for i in range( len( scrambled_movement_value_list ) ):
			rand_index = random.randint( 0, len( scrambled_movement_value_list ) - 1 )
			( scrambled_movement_value_list[ rand_index ], scrambled_movement_value_list[ i ] ) = ( 
				scrambled_movement_value_list[ i ], scrambled_movement_value_list[ rand_index ] )

		self.queue.put( scrambled_movement_value_list )
		self.queue.task_done()

def main():
	profile_total_time = 0.0
	# profile_time_in_swap = 0.0
	profile_time_in_enumerate = 0.0

	profile_total_time_begin = time.process_time()

	# ordered_movement_ordered_movement_value_list here is an ordered representation of the MOVEMENT_VALUE_MAP from above.
	ordered_movement_value_list = []
	for value in MOVEMENT_VALUE_MAP.keys():
		ordered_movement_value_list += ( [ value, ] * MOVEMENT_VALUE_MAP[ value ] )


	# This is a list of, for every simulation, the number of turns it took to exceed TARGET_DISTANCE above.
	turns_to_finish_list = []

	# ...and this is a map from the number of turns it took to exceed TARGET_DISTANCE to the number of times
	#	that count came up across all simulations. 
	turns_to_finish_count_map = {}


	profile_time_before_swap = time.process_time()

	NUM_SWAP_THREADS = 5
	this_queue = queue.Queue()
	thread_pool = []
	for i in range( NUM_SWAP_THREADS ):
		thread_pool.append( ListScrambleWorker( this_queue, ordered_movement_value_list ) )

	while( len( turns_to_finish_list ) < NUM_TIMES_TO_EXECUTE ):
		for thread in thread_pool:
			if( not thread.is_alive() ):
				# print "Kicking off thread {}".format( len( turns_to_finish_list ) )
				thread.run()

		while( not this_queue.empty() ):
			scrambled_movement_value_list = this_queue.get()

			profile_time_between_swap_and_enumerate = time.process_time()
			# Now just count through the "shuffled" sequence of cards until you break your target movement. 
			summed_value = 0
			for( turn_ctr, value ) in enumerate( scrambled_movement_value_list, 1 ):
				summed_value += value

				# If you've gone over, then note down the time it took this sequence to finish.
				if( summed_value >= TARGET_DISTANCE ):
					turns_to_finish_list.append( turn_ctr )
					if( turn_ctr not in turns_to_finish_count_map ):
						turns_to_finish_count_map[ turn_ctr ] = 1
					else:
						turns_to_finish_count_map[ turn_ctr ] += 1
					break
			profile_time_after_enumerate = time.process_time()
			profile_time_in_enumerate += profile_time_after_enumerate - profile_time_between_swap_and_enumerate

	print( "Average number of cards: {}".format( float(sum(turns_to_finish_list))/len(turns_to_finish_list) ) )

	keys_list = list(turns_to_finish_count_map.keys())
	keys_list.sort()
	for key in keys_list:
		num_times = turns_to_finish_count_map[key]
		percent = float( num_times ) / len( turns_to_finish_list ) * 100.0
		print ("Num at {key}: {num_times} ({percent}%)".format( **vars() ) )

	profile_total_time_end = time.process_time()
	profile_total_time = profile_total_time_end - profile_total_time_begin

	print( '''Total time in process: {profile_total_time}
Time in enumerate: {profile_time_in_enumerate}'''.format( **vars() ) )

if( __name__ == "__main__" ):
	main()