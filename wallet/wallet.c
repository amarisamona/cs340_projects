/**
 * A sorted array-based map.
 *
 * Get: O(log n)
 * Change: O(log n)
 * Insert: O(n)
 * Remove: not implemented
 */
#define _POSIX_C_SOURCE 200809L
#include <time.h>
#include <stdlib.h>
#include <limits.h>
#include <string.h>
#include "wallet.h"


typedef struct m_entry {
  const char *key;
  int val;
  pthread_mutex_t *lock;
  pthread_cond_t *cond;
} m_entry;


void m_init(my_map *map) {
  map->capacity = 4;
  map->size = 0;
  map->array = malloc(sizeof(m_entry) * map->capacity);
  pthread_rwlock_init(&map->rwlock, NULL); /* initialize the reader writer lock */
}

void m_free(my_map *map) {
  for (unsigned int i = 0; i < map->size; ++i) {
    pthread_mutex_destroy(map->array[i].lock);
    free(map->array[i].lock);
    
    pthread_cond_destroy(map->array[i].cond);
    free(map->array[i].cond);
  }
  free(map->array); /* frees the keys and values */
  map->size = 0;
  map->capacity = 0;
  // pthread_rwlock_destroy(&map->rwlock);
}

/**
 * Helper method, using binary search.
 *
 * If key is in the map, returns true and sets index_to_set to the index of the key in the array.
 * Otherwise, returns false and sets index_to_set to the index where it ought to appear if added.
 */
static bool m_find(const my_map *map, const char *key, int *index_to_set) {
  int low = 0, high = map->size;
  while (low < high) {
    int i = (low+high)>>1;
    int diff = strcmp(key, map->array[i].key);
    if (diff == 0){
      *index_to_set = i;
      return true;
    }
    if (diff < 0) low = i+1;
    else high = i;
  }
  *index_to_set = low;
  return false;
} /* no need to meddle with this */

/**
 * If the key is in the map, returns its current value.
 * Otherwise, inserts it with value `def` and returns `def`.
 * 
 * Keys are not copied, nor are their memory freed by w_free.
 * It is the caller's responsibility to ensure that the key pointer
 * remains valid and points to the same sequence of characters
 * for the entire lifespan of the map.
 */
int m_setdefault(my_map *map, const char *key, int def) {
  
  int idx;
  pthread_rwlock_rdlock(&map->rwlock); //lock reader
  
  //sets idx to the index of the key
  bool found = m_find(map, key, &idx);
  if (found) {
    int val = map->array[idx].val;
    pthread_rwlock_unlock(&map->rwlock); //unlock reader lock and exit, it's in map
    return val;
  }
  pthread_rwlock_unlock(&map->rwlock);

  pthread_rwlock_wrlock(&map->rwlock); //get the writer lock to insert
  found = m_find(map, key, &idx); //another thread couldve added the value!
  if (found) {
    int val2 = map->array[idx].val;
    pthread_rwlock_unlock(&map->rwlock); //double check and exit early if another thread added key
    return val2;
  }

  // make space if needed
  if (map->size == map->capacity) {
    map->capacity *= 2;
    map->array = realloc(map->array, sizeof(m_entry) * map->capacity);
  }

  // make a hole for the new entry
  for (int i = map->size; i>idx; i-=1){
    map->array[i] = map->array[i-1];
  }
  map->size += 1;

  // insert into array
  map->array[idx].key = key;
  map->array[idx].val = def;
  map->array[idx].lock = malloc(sizeof(pthread_mutex_t));
  pthread_mutex_init(map->array[idx].lock, NULL);
  map->array[idx].cond = malloc(sizeof(pthread_cond_t));
  pthread_cond_init(map->array[idx].cond, NULL);

  pthread_rwlock_unlock(&map->rwlock); //unlock writer
  return def;
}

/**
 * If the key is in the map, sets its value to `val` and returns true.
 * Otherwise, does not modify the map and returns false.
 */
bool m_assign(my_map *map, const char *key, int val){
  int idx;
  pthread_rwlock_rdlock(&map->rwlock);
  bool found = m_find(map, key, &idx);
  if (!found) {
    pthread_rwlock_unlock(&map->rwlock);
    return false;
  }
  map->array[idx].val = val;
  pthread_rwlock_unlock(&map->rwlock);
  return true;
}


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

int wallet_use(my_map *map, const char *key, int delta) {

  int idx;
  m_setdefault(map, key, 0); /* if not in array, inserts with 0 */

  pthread_rwlock_rdlock(&map->rwlock);
  m_find(map, key, &idx);

  pthread_mutex_t *mute = map->array[idx].lock;
  pthread_cond_t *cond = map->array[idx].cond;
  m_entry *e = &map->array[idx];

  pthread_mutex_lock(mute);

  while (e->val + delta < 0) {
    pthread_rwlock_unlock(&map->rwlock);
    pthread_cond_wait(cond, mute);
    pthread_rwlock_rdlock(&map->rwlock);
    m_find(map, key, &idx);
    e = &map->array[idx];
  } 

  e->val += delta;
  int result = e->val;

  pthread_cond_broadcast(cond);
  pthread_mutex_unlock(mute);

  pthread_rwlock_unlock(&map->rwlock);

  return result;
}
