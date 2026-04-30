/* navigation.c
   Safe two-pass adjacency builder + improved input resolution:
   - extracts node_<digits> if present
   - extracts (lat,lon) inside parentheses if present
   - supports numeric OSM id, "lat,lon", or substring label (case-insensitive)
   - writes last_route.json
   Compile:
     gcc navigation.c -O2 -o navigation.exe -lm
*/

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>

typedef long long ll;
#define INF 1e18
#define MAXPATH 131072

/* Node info */
typedef struct {
    ll osm_id;
    double lat, lon;
    char *label;
    int has_loc;
} NodeInfo;

/* Temp edge (as read) */
typedef struct {
    ll u, v;
    double dist;
    double safety;
} TempEdge;

/* adjacency edge */
typedef struct {
    int to;
    double dist;
    double safety;
} AdjEdge;

/* adjacency list */
typedef struct {
    AdjEdge *arr;
    int size;
    int cap;
} AdjList;

/* simple open-addressing ID map (ll -> int) */
typedef struct { ll key; int val; char used; } MapEntry;
typedef struct { MapEntry *entries; int cap; int count; } IDMap;

/* hashing (64-bit mix) */
static unsigned long long mix64(unsigned long long z){
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    z = z ^ (z >> 31);
    return z;
}
int idmap_init(IDMap *m, int capacity){
    m->cap = 1; while(m->cap < capacity) m->cap <<= 1;
    m->entries = calloc(m->cap, sizeof(MapEntry));
    if(!m->entries) return 0;
    m->count = 0; return 1;
}
void idmap_free(IDMap *m){ if(m->entries) free(m->entries); m->entries=NULL; m->cap=m->count=0; }
int idmap_put(IDMap *m, ll key, int val){
    if(!m->entries) return 0;
    if((double)(m->count + 1) / (double)m->cap > 0.7){
        int oldcap = m->cap; MapEntry *old = m->entries;
        int newcap = oldcap * 2; MapEntry *ne = calloc(newcap, sizeof(MapEntry));
        if(!ne) return 0;
        m->entries = ne; m->cap = newcap; m->count = 0;
        for(int i=0;i<oldcap;i++) if(old[i].used){
            unsigned long long h = mix64((unsigned long long)old[i].key);
            int idx = h & (m->cap - 1);
            while(m->entries[idx].used) idx = (idx+1) & (m->cap - 1);
            m->entries[idx].used = 1; m->entries[idx].key = old[i].key; m->entries[idx].val = old[i].val; m->count++;
        }
        free(old);
    }
    unsigned long long h = mix64((unsigned long long)key);
    int idx = h & (m->cap - 1);
    while(m->entries[idx].used){
        if(m->entries[idx].key == key){ m->entries[idx].val = val; return 1; }
        idx = (idx+1) & (m->cap - 1);
    }
    m->entries[idx].used = 1; m->entries[idx].key = key; m->entries[idx].val = val; m->count++;
    return 1;
}
int idmap_get(IDMap *m, ll key){
    if(!m->entries) return -1;
    unsigned long long h = mix64((unsigned long long)key);
    int idx = h & (m->cap - 1);
    int start = idx;
    while(m->entries[idx].used){
        if(m->entries[idx].key == key) return m->entries[idx].val;
        idx = (idx+1) & (m->cap - 1);
        if(idx == start) break;
    }
    return -1;
}

/* Globals built after reading CSVs */
NodeInfo *nodes = NULL;
int node_cap = 0;
int node_count = 0;
AdjList *adj = NULL;
IDMap idmap = {NULL,0,0};

/* helpers */
void trim_nl(char *s){ size_t L=strlen(s); while(L && (s[L-1]=='\n' || s[L-1]=='\r')) s[--L]=0; }
char *strdup_safe(const char *s){ if(!s) return NULL; char *p = malloc(strlen(s)+1); strcpy(p,s); return p; }

int ensure_node_cap(int need){
    if(node_cap >= need) return 1;
    int nc = node_cap?node_cap:256;
    while(nc < need) nc *= 2;
    NodeInfo *tmp = realloc(nodes, sizeof(NodeInfo) * nc);
    if(!tmp) return 0;
    nodes = tmp;
    for(int i=node_cap;i<nc;i++){ nodes[i].osm_id = 0; nodes[i].lat = nodes[i].lon = 0.0; nodes[i].label = NULL; nodes[i].has_loc = 0; }
    node_cap = nc; return 1;
}

/* Haversine distance (meters) */
double haversine_m(double lat1, double lon1, double lat2, double lon2){
    const double R = 6371000.0;
    double dlat = (lat2 - lat1) * M_PI / 180.0;
    double dlon = (lon2 - lon1) * M_PI / 180.0;
    double a = sin(dlat/2.0)*sin(dlat/2.0) + cos(lat1*M_PI/180.0)*cos(lat2*M_PI/180.0)*sin(dlon/2.0)*sin(dlon/2.0);
    double c = 2 * atan2(sqrt(a), sqrt(1-a));
    return R * c;
}

/* load nodes.csv (node_id,lat,lon,label) */
int load_nodes_csv(const char *path){
    FILE *f = fopen(path,"r"); if(!f) return 0;
    char line[1024];
    if(!fgets(line,sizeof(line),f)){ fclose(f); return 0; } /* header */
    while(fgets(line,sizeof(line),f)){
        trim_nl(line); if(line[0]==0) continue;
        char *p = line; char *tok[4]; int ti=0;
        char *t = strtok(p, ",\n\r");
        while(t && ti < 4){ while(*t && isspace((unsigned char)*t)) t++; char *end = t + strlen(t) - 1; while(end > t && isspace((unsigned char)*end)) { *end = 0; end--; } tok[ti++] = t; t = strtok(NULL, ",\n\r"); }
        if(ti < 3) continue;
        ll nid = atoll(tok[0]);
        double lat = atof(tok[1]);
        double lon = atof(tok[2]);
        char *label = (ti >= 4) ? strdup_safe(tok[3]) : NULL;
        int idx = idmap_get(&idmap, nid);
        if(idx == -1){
            idx = node_count;
            if(!ensure_node_cap(node_count+1)){ fclose(f); return 0; }
            nodes[idx].osm_id = nid; nodes[idx].lat = lat; nodes[idx].lon = lon; nodes[idx].label = label; nodes[idx].has_loc = 1;
            if(!idmap_put(&idmap, nid, idx)){ fclose(f); return 0; }
            node_count++;
        } else {
            nodes[idx].lat = lat; nodes[idx].lon = lon; nodes[idx].has_loc = 1;
            if(label){ if(nodes[idx].label) free(nodes[idx].label); nodes[idx].label = label; }
        }
    }
    fclose(f); return 1;
}

/* read graph CSV into temp edge array (u,v,dist,safety) */
TempEdge *read_graph_temp(const char *path, int *out_m){
    FILE *f = fopen(path,"r"); if(!f) return NULL;
    char line[1024];
    if(!fgets(line,sizeof(line),f)){ fclose(f); return NULL; } /* header */
    int cap = 65536; int m = 0;
    TempEdge *arr = malloc(sizeof(TempEdge) * cap);
    while(fgets(line,sizeof(line),f)){
        trim_nl(line); if(line[0]==0) continue;
        char *p=line; char *tok;
        tok = strtok(p, ",\n\r"); if(!tok) continue; ll u = atoll(tok);
        tok = strtok(NULL, ",\n\r"); if(!tok) continue; ll v = atoll(tok);
        tok = strtok(NULL, ",\n\r"); if(!tok) continue; double d = atof(tok);
        tok = strtok(NULL, ",\n\r"); double safety = 50.0; if(tok) safety = atof(tok);
        if(m >= cap){ cap *= 2; TempEdge *tmp = realloc(arr, sizeof(TempEdge) * cap); if(!tmp){ free(arr); fclose(f); return NULL; } arr = tmp; }
        arr[m].u = u; arr[m].v = v; arr[m].dist = d; arr[m].safety = safety; m++;
        if(idmap_get(&idmap, u) == -1){
            int idx = node_count;
            if(!ensure_node_cap(node_count+1)){}
            nodes[idx].osm_id = u; nodes[idx].has_loc = 0; nodes[idx].label = NULL; nodes[idx].lat = nodes[idx].lon = 0.0;
            idmap_put(&idmap, u, idx); node_count++;
        }
        if(idmap_get(&idmap, v) == -1){
            int idx = node_count;
            if(!ensure_node_cap(node_count+1)){}
            nodes[idx].osm_id = v; nodes[idx].has_loc = 0; nodes[idx].label = NULL; nodes[idx].lat = nodes[idx].lon = 0.0;
            idmap_put(&idmap, v, idx); node_count++;
        }
    }
    fclose(f);
    *out_m = m; return arr;
}

/* Build adjacency lists in two passes */
int build_adjacency(TempEdge *edges, int m){
    if(node_count <= 0) return 0;
    adj = calloc(node_count, sizeof(AdjList));
    if(!adj) return 0;
    int *deg = calloc(node_count, sizeof(int));
    if(!deg){ free(adj); adj = NULL; return 0; }
    for(int i=0;i<m;i++){
        int a = idmap_get(&idmap, edges[i].u);
        int b = idmap_get(&idmap, edges[i].v);
        if(a < 0 || b < 0) continue;
        deg[a]++; deg[b]++;
    }
    for(int i=0;i<node_count;i++){
        adj[i].cap = deg[i];
        adj[i].size = 0;
        if(deg[i] > 0){
            adj[i].arr = malloc(sizeof(AdjEdge) * deg[i]);
            if(!adj[i].arr){ for(int j=0;j<i;j++) if(adj[j].arr) free(adj[j].arr); free(adj); adj=NULL; free(deg); return 0; }
        } else adj[i].arr = NULL;
    }
    for(int i=0;i<m;i++){
        int a = idmap_get(&idmap, edges[i].u);
        int b = idmap_get(&idmap, edges[i].v);
        if(a < 0 || b < 0) continue;
        adj[a].arr[adj[a].size].to = b; adj[a].arr[adj[a].size].dist = edges[i].dist; adj[a].arr[adj[a].size].safety = edges[i].safety; adj[a].size++;
        adj[b].arr[adj[b].size].to = a; adj[b].arr[adj[b].size].dist = edges[i].dist; adj[b].arr[adj[b].size].safety = edges[i].safety; adj[b].size++;
    }
    free(deg); return 1;
}

/* heap */
typedef struct { int node; double cost; } HItem;
typedef struct { HItem *arr; int size, cap; } MinHeap;
MinHeap *heap_create(int cap){ MinHeap*h=malloc(sizeof(MinHeap)); h->arr=malloc(sizeof(HItem)*cap); h->size=0; h->cap=cap; return h; }
void heap_free(MinHeap*h){ if(!h) return; free(h->arr); free(h); }
void heap_push(MinHeap*h,int node,double cost){
    if(h->size >= h->cap){ int nc = h->cap*2; HItem*tmp = realloc(h->arr, sizeof(HItem)*nc); if(!tmp){ fprintf(stderr,"heap realloc fail\n"); exit(1);} h->arr = tmp; h->cap = nc; }
    int i = h->size++; h->arr[i].node = node; h->arr[i].cost = cost;
    while(i>0){ int p=(i-1)/2; if(h->arr[p].cost <= h->arr[i].cost) break; HItem t=h->arr[p]; h->arr[p]=h->arr[i]; h->arr[i]=t; i=p; }
}
int heap_pop(MinHeap*h,int*out_node,double*out_cost){
    if(h->size==0) return 0; HItem top = h->arr[0]; h->size--;
    if(h->size>0){ h->arr[0] = h->arr[h->size]; int i=0; while(1){ int l=2*i+1,r=2*i+2,s=i; if(l<h->size && h->arr[l].cost < h->arr[s].cost) s=l; if(r<h->size && h->arr[r].cost < h->arr[s].cost) s=r; if(s==i) break; HItem t=h->arr[i]; h->arr[i]=h->arr[s]; h->arr[s]=t; i=s; } }
    if(out_node) *out_node = top.node; if(out_cost) *out_cost = top.cost; return 1;
}

/* Dijkstra */
int dijkstra(int src,int dst,int mode,double alpha,int **out_path,int *out_len,double *out_total_dist,double *out_avg_safety){
    if(src<0 || dst<0) return 0;
    int n = node_count;
    double *dist = malloc(sizeof(double)*n);
    int *prev = malloc(sizeof(int)*n);
    char *vis = calloc(n,1);
    if(!dist||!prev||!vis){ free(dist); free(prev); free(vis); return 0; }
    for(int i=0;i<n;i++){ dist[i]=INF; prev[i]=-1; }
    dist[src]=0.0;
    MinHeap *h = heap_create(256); heap_push(h, src, 0.0);
    while(h->size>0){
        int u; double c; if(!heap_pop(h,&u,&c)) break;
        if(c > dist[u] + 1e-12) continue;
        if(vis[u]) continue; vis[u] = 1;
        if(u == dst) break;
        for(int ei=0; ei<adj[u].size; ei++){
            AdjEdge e = adj[u].arr[ei];
            double cost = e.dist;
            if(mode == 2){ double penalty = (100.0 - e.safety); cost = e.dist + alpha * penalty; }
            if(dist[u] + cost < dist[e.to]){
                dist[e.to] = dist[u] + cost;
                prev[e.to] = u;
                heap_push(h, e.to, dist[e.to]);
            }
        }
    }
    if(dist[dst] >= INF/2){ heap_free(h); free(dist); free(prev); free(vis); return 0; }
    int tmp[MAXPATH]; int plen=0; int cur=dst;
    while(cur!=-1 && plen<MAXPATH){ tmp[plen++] = cur; cur = prev[cur]; }
    int *path = malloc(sizeof(int)*plen);
    for(int i=0;i<plen;i++) path[i] = tmp[plen-1-i];
    double tot_dist=0.0, tot_safety=0.0; int ecount=0;
    for(int i=0;i<plen-1;i++){
        int a = path[i], b = path[i+1];
        for(int j=0;j<adj[a].size;j++){
            AdjEdge e = adj[a].arr[j];
            if(e.to == b){ tot_dist += e.dist; tot_safety += e.safety; ecount++; break; }
        }
    }
    *out_path = path; *out_len = plen; *out_total_dist = tot_dist; *out_avg_safety = ecount ? (tot_safety/ecount) : 0.0;
    heap_free(h); free(dist); free(prev); free(vis);
    return 1;
}

/* write last_route.json */
void write_last_route_json(const char *fname, int *path, int plen, double total_distance, double avg_safety, int mode, double alpha){
    FILE *f = fopen(fname,"w"); if(!f) return;
    fprintf(f, "{\n  \"mode\": \"%s\",\n  \"alpha\": %.6f,\n  \"total_distance_km\": %.6f,\n  \"avg_safety\": %.6f,\n  \"nodes\": [\n", mode==1?"Fastest":"Safest", alpha, total_distance, avg_safety);
    for(int i=0;i<plen;i++){
        int idx = path[i];
        fprintf(f, "    { \"node_id\": %lld, \"lat\": %.6f, \"lon\": %.6f, \"label\": \"%s\" }%s\n",
            nodes[idx].osm_id, nodes[idx].has_loc ? nodes[idx].lat : 0.0, nodes[idx].has_loc ? nodes[idx].lon : 0.0,
            nodes[idx].label ? nodes[idx].label : "", (i==plen-1) ? "" : ",");
    }
    fprintf(f, "  ],\n  \"edges\": [\n");
    for(int i=0;i<plen-1;i++){
        int a = path[i], b = path[i+1], found = 0;
        for(int j=0;j<adj[a].size;j++){
            AdjEdge e = adj[a].arr[j];
            if(e.to == b){
                fprintf(f, "    { \"from\": %lld, \"to\": %lld, \"distance_km\": %.6f, \"safety\": %.2f }%s\n",
                    nodes[a].osm_id, nodes[b].osm_id, e.dist, e.safety, (i==plen-2)?"":",");
                found = 1; break;
            }
        }
        if(!found) fprintf(f, "    { \"from\": %lld, \"to\": %lld, \"distance_km\": null, \"safety\": null }%s\n",
            nodes[a].osm_id, nodes[b].osm_id, (i==plen-2)?"":",");
    }
    fprintf(f, "  ]\n}\n"); fclose(f);
}

/* Helper: trim leading/trailing whitespace in-place */
static void trim_ws_inplace(char *s){
    if(!s) return;
    char *start = s;
    while(*start && isspace((unsigned char)*start)) start++;
    if(start != s) memmove(s, start, strlen(start)+1);
    size_t L = strlen(s);
    while(L > 0 && isspace((unsigned char)s[L-1])) s[--L] = 0;
}

/* parse input: improved:
   - extract node_<digits> anywhere and treat as numeric id
   - extract (lat,lon) inside parentheses
   - numeric OSM id as string
   - direct "lat,lon"
   - substring label search (case-insensitive)
*/
int parse_input_to_index(const char *s_in){
    if(!s_in) return -1;
    char s[512];
    strncpy(s, s_in, sizeof(s)-1); s[sizeof(s)-1]=0;
    trim_ws_inplace(s);
    if(s[0] == '"' || s[0] == '\''){
        /* strip surrounding quotes if present */
        size_t L = strlen(s);
        if((s[L-1] == '"' || s[L-1] == '\'') && L > 1) s[L-1]=0, memmove(s, s+1, L-1);
    }

    /* 1) look for "node_<digits>" anywhere (case-insensitive) */
    char lower[512]; size_t i;
    for(i=0;i<strlen(s) && i < sizeof(lower)-1;i++) lower[i] = tolower((unsigned char)s[i]);
    lower[i]=0;
    char *pos = strstr(lower, "node_");
    if(pos){
        /* pos points into lower; find digits after "node_" */
        char *digits = pos + 5; /* in lower */
        /* map digits pointer back to original string position */
        int offset = (int)(digits - lower);
        char *orig_digits = s + offset;
        /* parse digits */
        char *p = orig_digits;
        while(*p && !isdigit((unsigned char)*p)) p++;
        if(isdigit((unsigned char)*p)){
            char *endp = p;
            while(*endp && isdigit((unsigned char)*endp)) endp++;
            char tmp = *endp; *endp = 0;
            ll id = atoll(p);
            *endp = tmp;
            int idx = idmap_get(&idmap, id);
            if(idx != -1) return idx;
            /* if not found, continue to other attempts */
        }
    }

    /* 2) try numeric OSM id (whole string) */
    char *endptr = NULL;
    ll v = strtoll(s, &endptr, 10);
    if(endptr != s && *endptr == '\0'){
        int idx = idmap_get(&idmap, v);
        if(idx != -1) return idx;
        /* else continue */
    }

    /* 3) try to extract (lat,lon) inside parentheses: e.g. "node_123 (18.44,73.88)" */
    char *lpar = strchr(s, '(');
    if(lpar){
        double lat=0, lon=0;
        if(sscanf(lpar, " (%lf , %lf", &lat, &lon) == 2 || sscanf(lpar, "(%lf,%lf", &lat,&lon) == 2){
            double bestd = 1e99; int besti = -1;
            for(int i=0;i<node_count;i++){
                if(!nodes[i].has_loc) continue;
                double d = haversine_m(lat, lon, nodes[i].lat, nodes[i].lon);
                if(d < bestd){ bestd = d; besti = i; }
            }
            if(besti >= 0) return besti;
        }
    }

    /* 4) try direct "lat,lon" pair */
    double lat=0, lon=0;
    if(sscanf(s, "%lf , %lf", &lat, &lon) == 2 || sscanf(s, "%lf,%lf", &lat,&lon) == 2){
        double bestd = 1e99; int besti = -1;
        for(int i=0;i<node_count;i++){
            if(!nodes[i].has_loc) continue;
            double d = haversine_m(lat, lon, nodes[i].lat, nodes[i].lon);
            if(d < bestd){ bestd = d; besti = i; }
        }
        if(besti >= 0) return besti;
    }

    /* 5) substring name search (case-insensitive) */
    int qlen = strlen(s);
    if(qlen > 0){
        for(int i=0;i<node_count;i++){
            if(nodes[i].label){
                const char *name = nodes[i].label;
                /* case-insensitive substring search */
                for(int p=0; name[p]; p++){
                    int match = 1;
                    for(int k=0;k<qlen;k++){
                        if(name[p+k]==0 || tolower((unsigned char)name[p+k]) != tolower((unsigned char)s[k])){ match = 0; break; }
                    }
                    if(match) return i;
                }
            }
        }
    }

    return -1;
}

/* main and other code unchanged from earlier */
int main(int argc, char **argv){
    const char *graph_path=NULL, *nodes_path=NULL, *src_str=NULL, *dst_str=NULL;
    int mode = 1; double alpha = 2.0;
    for(int i=1;i<argc;i++){
        if(strcmp(argv[i],"--graph")==0 && i+1<argc) graph_path = argv[++i];
        else if(strncmp(argv[i],"--graph=",8)==0) graph_path = argv[i]+8;
        else if(strcmp(argv[i],"--nodes")==0 && i+1<argc) nodes_path = argv[++i];
        else if(strncmp(argv[i],"--nodes=",8)==0) nodes_path = argv[i]+8;
        else if(strcmp(argv[i],"--src")==0 && i+1<argc) src_str = argv[++i];
        else if(strncmp(argv[i],"--src=",6)==0) src_str = argv[i]+6;
        else if(strcmp(argv[i],"--dst")==0 && i+1<argc) dst_str = argv[++i];
        else if(strncmp(argv[i],"--dst=",6)==0) dst_str = argv[i]+6;
        else if(strcmp(argv[i],"--mode")==0 && i+1<argc) mode = atoi(argv[++i]);
        else if(strncmp(argv[i],"--mode=",7)==0) mode = atoi(argv[i]+7);
        else if(strcmp(argv[i],"--alpha")==0 && i+1<argc) alpha = atof(argv[++i]);
        else if(strncmp(argv[i],"--alpha=",8)==0) alpha = atof(argv[i]+8);
    }

    if(!idmap_init(&idmap, 32768)){ fprintf(stderr,"idmap init failed\n"); return 1; }
    if(!ensure_node_cap(256)){ fprintf(stderr,"node cap init failed\n"); return 1; }

    if(nodes_path){
        if(!load_nodes_csv(nodes_path)){ fprintf(stderr,"Failed to load nodes CSV: %s\n", nodes_path); return 1; }
    }

    if(!graph_path){ fprintf(stderr,"Missing --graph <path>\n"); return 1; }
    int m = 0;
    TempEdge *tmpedges = read_graph_temp(graph_path, &m);
    if(!tmpedges){ fprintf(stderr,"Failed to read graph CSV: %s\n", graph_path); return 1; }

    if(!build_adjacency(tmpedges, m)){ fprintf(stderr,"Failed building adjacency\n"); free(tmpedges); return 1; }

    if(!src_str || !dst_str){ fprintf(stderr,"Missing --src or --dst\n"); free(tmpedges); return 1; }

    int src = parse_input_to_index(src_str);
    int dst = parse_input_to_index(dst_str);

    /* Debug: print resolution info */
    if(src >= 0){
        fprintf(stderr, "[resolve] src input='%s' -> index=%d osm_id=%lld label='%s' lat=%.6f lon=%.6f\n",
            src_str, src, nodes[src].osm_id, nodes[src].label?nodes[src].label:"", nodes[src].has_loc?nodes[src].lat:0.0, nodes[src].has_loc?nodes[src].lon:0.0);
    } else {
        fprintf(stderr, "[resolve] src input='%s' -> NOT FOUND\n", src_str);
    }
    if(dst >= 0){
        fprintf(stderr, "[resolve] dst input='%s' -> index=%d osm_id=%lld label='%s' lat=%.6f lon=%.6f\n",
            dst_str, dst, nodes[dst].osm_id, nodes[dst].label?nodes[dst].label:"", nodes[dst].has_loc?nodes[dst].lat:0.0, nodes[dst].has_loc?nodes[dst].lon:0.0);
    } else {
        fprintf(stderr, "[resolve] dst input='%s' -> NOT FOUND\n", dst_str);
    }

    if(src < 0 || dst < 0){ fprintf(stderr,"Error: could not map src/dst to known nodes (check IDs, coords or names).\n"); free(tmpedges); return 2; }

    int *path = NULL; int plen = 0; double tot_dist=0.0, avg_safety=0.0;
    if(!dijkstra(src, dst, mode, alpha, &path, &plen, &tot_dist, &avg_safety)){ fprintf(stderr,"No path found\n"); free(tmpedges); return 2; }

    printf("{ \"ok\": true, \"mode\": \"%s\", \"total_distance_km\": %.6f, \"avg_safety\": %.6f }\n", mode==1?"Fastest":"Safest", tot_dist, avg_safety);
    write_last_route_json("last_route.json", path, plen, tot_dist, avg_safety, mode, alpha);

    free(path); free(tmpedges);
    /* cleanup */
    idmap_free(&idmap);
    for(int i=0;i<node_count;i++) if(nodes[i].label) free(nodes[i].label);
    if(nodes) free(nodes);
    if(adj){ for(int i=0;i<node_count;i++) if(adj[i].arr) free(adj[i].arr); free(adj); }
    return 0;
}
