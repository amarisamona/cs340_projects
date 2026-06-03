/**
 * A sorted array-based map, around which a synchronized wallet is built.
 * 
 * The starter files provided by CS 340 course staff implement a map
 * with C-string keys and int values, which has the following properties:
 *
 * Get: O(log n)
 * Change: O(log n)
 * Insert: O(n)
 * Remove: not implemented
 * 
 * Students should add to this map the synchronization and wallet change operations.
 */

#include <stdbool.h> // bool type, true and false literals
#include <pthread.h>

typedef struct m_entry m_entry;

typedef struct {
  unsigned capacity;
  unsigned size;
  m_entry *array;
  // TO DO: add synchronization primitives here and/or in the m_entry struct in wallet.c
  pthread_rwlock_t rwlock;
} my_map;

void m_init(my_map *map);
void m_free(my_map *map);

/**
 * If the key is in the map, returns its current value.
 * Otherwise, inserts it with value `def` and returns `def`.
 * 
 * Keys are not copied, nor are their memory freed by m_free.
 * It is the caller's responsibility to ensure that the key pointer
 * remains valid and points to the same sequence of characters
 * for the entire lifespan of the map if it is inserted here.
 */
int m_setdefault(my_map *map, const char *key, int def);

/**
 * If the key is in the map, sets its value to `val` and returns true.
 * Otherwise, does not modify the map and returns false.
 */
bool m_assign(my_map *map, const char *key, int val);


/**
 * Modify a map entry by a given delta, conceptually like
 * 
 * if key not in map, map[key] = 0
 * then, map[key] += delta
 * 
 * with the caveat that if the change would make the value negative,
 * the function blocks until that is no longer the case.
 * 
 * Returns the newly-assigned value.
 */
int wallet_use(my_map *map, const char *key, int delta);
