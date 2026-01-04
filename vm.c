#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_STACK 4096
#define MAX_VARS 1024
#define MAX_LABELS 1024
#define MAX_LINES 8192
#define LINE_BUF_SIZE 2048

void panic(const char *msg) { fprintf(stderr, "Panic: %s\n", msg); exit(1); }

// --- Type System ---
typedef enum { OBJ_INT, OBJ_STR, OBJ_LIST, OBJ_DICT, OBJ_NONE } ObjType;

// Forward declarations
struct List;
struct Dict;

// Object Definition (Moved to top)
typedef struct Object {
    ObjType type;
    union {
        int i;
        char *s;
        struct List *l;
        struct Dict *d;
    } v;
} Object;

// List Implementation
typedef struct List {
    Object *items;
    int count;
    int capacity;
} List;

// Dict Implementation
typedef struct {
    char *key;
    Object val; // Now Object is defined, so this is valid
} KVPair;

typedef struct Dict {
    KVPair *pairs;
    int count;
    int capacity;
} Dict;

// --- Memory Constructors ---
Object make_int(int v) { Object o; o.type=OBJ_INT; o.v.i=v; return o; }
Object make_none() { Object o; o.type=OBJ_NONE; return o; }

Object make_str(const char *s) { 
    Object o; o.type=OBJ_STR; 
    o.v.s = s ? strdup(s) : strdup(""); 
    return o; 
}

Object make_list() {
    Object o; o.type=OBJ_LIST;
    o.v.l = malloc(sizeof(List));
    o.v.l->items = malloc(sizeof(Object)*8);
    o.v.l->count=0; o.v.l->capacity=8;
    return o;
}

Object make_dict() {
    Object o; o.type=OBJ_DICT;
    o.v.d = malloc(sizeof(Dict));
    o.v.d->pairs = malloc(sizeof(KVPair)*8);
    o.v.d->count=0; o.v.d->capacity=8;
    return o;
}

// --- Data Structures ---
Object stack[MAX_STACK];
int sp = 0;

typedef struct { char name[64]; Object val; } Variable;
Variable vars[MAX_VARS];
int var_count = 0;

typedef struct { char name[64]; int line_num; } Label;
Label labels[MAX_LABELS];
int label_count = 0;

char program[MAX_LINES][LINE_BUF_SIZE];
int prog_size = 0;

// --- Stack Ops ---
void push(Object obj) { if(sp>=MAX_STACK) panic("Stack overflow"); stack[sp++] = obj; }
Object pop() { if(sp<=0) panic("Stack underflow"); return stack[--sp]; }
Object peek() { if(sp<=0) panic("Stack underflow"); return stack[sp-1]; }

// --- Variable Ops ---
Object get_var(char *name) {
    for(int i=0; i<var_count; i++) if(strcmp(vars[i].name,name)==0) return vars[i].val;
    if(strcmp(name, "D")==0) { 
        Object d = make_dict(); 
        if(var_count<MAX_VARS) { strcpy(vars[var_count].name,name); vars[var_count].val=d; var_count++; }
        return d;
    }
    return make_none();
}

void set_var(char *name, Object val) {
    for(int i=0; i<var_count; i++) if(strcmp(vars[i].name,name)==0) { vars[i].val=val; return; }
    if(var_count>=MAX_VARS) panic("Var limit");
    strcpy(vars[var_count].name,name); vars[var_count].val=val; var_count++;
}

// --- List/Dict Ops ---
void list_append(List *l, Object item) {
    if(l->count == l->capacity) {
        l->capacity *= 2;
        l->items = realloc(l->items, sizeof(Object)*l->capacity);
    }
    l->items[l->count++] = item;
}

void dict_set(Dict *d, char *key, Object val) {
    for(int i=0; i<d->count; i++) {
        if(strcmp(d->pairs[i].key, key)==0) { d->pairs[i].val=val; return; }
    }
    if(d->count == d->capacity) {
        d->capacity *= 2;
        d->pairs = realloc(d->pairs, sizeof(KVPair)*d->capacity);
    }
    d->pairs[d->count].key = strdup(key);
    d->pairs[d->count].val = val;
    d->count++;
}

Object dict_get(Dict *d, char *key) {
    for(int i=0; i<d->count; i++) if(strcmp(d->pairs[i].key, key)==0) return d->pairs[i].val;
    return make_str(key);
}

// --- Helpers ---
int is_number(char *s) {
    if(*s=='-'||*s=='+')s++; if(!*s)return 0;
    while(*s) if(!isdigit(*s++))return 0; return 1;
}
int find_label(char *name) {
    for(int i=0; i<label_count; i++) if(strcmp(labels[i].name,name)==0) return labels[i].line_num;
    return -1;
}

// --- Built-in Methods ---
void call_method(char *method) {
    if (strcmp(method, "splitlines") == 0) {
        Object o = pop();
        if(o.type!=OBJ_STR) panic("splitlines on non-string");
        Object lst = make_list();
        char *dup = strdup(o.v.s);
        char *token = strtok(dup, "\n");
        while(token) { list_append(lst.v.l, make_str(token)); token = strtok(NULL, "\n"); }
        push(lst);
    }
    else if (strcmp(method, "strip") == 0) {
        Object arg = pop();
        Object o;
        if (arg.type == OBJ_STR) { 
             o = pop();
             char *s = o.v.s;
             char remove = arg.v.s[0];
             if(s[0] == remove) s++;
             int len = strlen(s);
             if(len>0 && s[len-1] == remove) s[len-1] = 0;
             push(make_str(s));
        } else {
             o = arg;
             char *start = o.v.s;
             while(isspace(*start)) start++;
             char *end = start + strlen(start) - 1;
             while(end > start && isspace(*end)) end--;
             *(end+1) = 0;
             push(make_str(start));
        }
    }
    else if (strcmp(method, "split") == 0) {
        Object top = pop();
        Object obj;
        char *sep = " ";
        if (top.type == OBJ_STR && sp > 0 && stack[sp-1].type == OBJ_STR) {
             obj = top;
             Object arg = pop();
             sep = arg.v.s;
        } else {
             obj = top;
        }
        
        Object lst = make_list();
        if(obj.type!=OBJ_STR) panic("split on non-str");
        char *dup = strdup(obj.v.s);
        char *token = strtok(dup, sep);
        while(token) { list_append(lst.v.l, make_str(token)); token = strtok(NULL, sep); }
        push(lst);
    }
    else if (strcmp(method, "join") == 0) {
        Object sep = pop();
        Object lst = pop();
        if(lst.type!=OBJ_LIST) panic("join on non-list");
        char buf[4096] = "";
        for(int i=0; i<lst.v.l->count; i++) {
            if(i>0) strcat(buf, sep.v.s);
            strcat(buf, lst.v.l->items[i].v.s);
        }
        push(make_str(buf));
    }
    else if (strcmp(method, "startswith") == 0) {
        Object obj = pop();
        Object arg = pop();
        if(strncmp(obj.v.s, arg.v.s, strlen(arg.v.s))==0) push(make_int(1)); else push(make_int(0));
    }
    else if (strcmp(method, "append") == 0) {
        Object lst = pop();
        Object item = pop();
        list_append(lst.v.l, item);
        push(make_none());
    }
    else if (strcmp(method, "format") == 0) {
        Object fmt = pop();
        Object arg = pop();
        char buf[1024];
        char *p = strstr(fmt.v.s, "{}");
        if(p) {
            int pre = p - fmt.v.s;
            strncpy(buf, fmt.v.s, pre); buf[pre]=0;
            if(arg.type==OBJ_INT) sprintf(buf+pre, "%d%s", arg.v.i, p+2);
            else sprintf(buf+pre, "%s%s", arg.v.s, p+2);
            push(make_str(buf));
        } else {
            push(fmt);
        }
    }
    else if (strcmp(method, "len") == 0) {
        Object o = pop();
        if(o.type==OBJ_LIST) push(make_int(o.v.l->count));
        else push(make_int(0));
    }
    else if (strcmp(method, "str") == 0) {
        Object o = pop();
        if(o.type==OBJ_INT) { char buf[32]; sprintf(buf, "%d", o.v.i); push(make_str(buf)); }
        else push(o);
    }
    else if (strcmp(method, "chr") == 0) {
        Object o = pop();
        char buf[2] = { (char)o.v.i, 0 };
        push(make_str(buf));
    }
    else if (strcmp(method, "read") == 0) {
    }
    else if (strcmp(method, "open") == 0) {
        Object path = pop();
        FILE *f = fopen(path.v.s, "r");
        if(f) {
            fseek(f, 0, SEEK_END); long fsize = ftell(f); fseek(f, 0, SEEK_SET);
            char *content = malloc(fsize + 1);
            fread(content, 1, fsize, f); content[fsize] = 0;
            fclose(f);
            push(make_str(content));
        } else {
            push(make_str(""));
        }
    }
}

int main(int argc, char *argv[]) {
    if (argc < 2) return 1;
    
    Object argv_list = make_list();
    list_append(argv_list.v.l, make_str("vm"));
    if(argc > 2) list_append(argv_list.v.l, make_str(argv[2]));
    
    Object sys_mod = make_dict();
    dict_set(sys_mod.v.d, "argv", argv_list);
    dict_set(sys_mod.v.d, "stderr", make_dict());
    
    strcpy(vars[var_count].name, "sys"); vars[var_count].val = sys_mod; var_count++;

    FILE *fp = fopen(argv[1], "r");
    if (!fp) return 1;

    char line[LINE_BUF_SIZE];
    while (fgets(line, sizeof(line), fp)) {
        line[strcspn(line, "\n")] = 0;
        if (strlen(line) == 0) continue;
        strcpy(program[prog_size], line);
        if (strncmp(line, "LABEL ", 6) == 0) {
            strcpy(labels[label_count].name, line + 6);
            labels[label_count].line_num = prog_size;
            label_count++;
        }
        prog_size++;
    }
    fclose(fp);

    int ip = 0;
    while (ip < prog_size) {
        char buf[LINE_BUF_SIZE];
        strcpy(buf, program[ip]);
        char *cmd = strtok(buf, " ");
        char *arg = strtok(NULL, "");
        if(arg) { while(*arg==' ') arg++; }
        ip++;

        if (!cmd || strcmp(cmd, "LABEL") == 0) {}
        else if (strcmp(cmd, "PUSH") == 0) {
            if (arg && is_number(arg)) push(make_int(atoi(arg)));
            else if (arg) push(make_str(arg));
            else push(make_int(0));
        }
        else if (strcmp(cmd, "STORE") == 0) set_var(arg, pop());
        else if (strcmp(cmd, "LOAD") == 0) push(get_var(arg));
        else if (strcmp(cmd, "PRINT") == 0) {
             Object o = pop();
             if(o.type==OBJ_STR) printf("%s\n", o.v.s);
             else printf("%d\n", o.v.i);
        }
        else if (strcmp(cmd, "ADD") == 0) {
             Object b = pop(); Object a = pop();
             if(a.type==OBJ_INT) push(make_int(a.v.i+b.v.i));
             else { 
                 char tmp[4096]; sprintf(tmp,"%s%s", a.v.s, b.v.s); 
                 push(make_str(tmp)); 
             }
        }
        else if (strcmp(cmd, "SUB") == 0) { Object b=pop(); Object a=pop(); push(make_int(a.v.i-b.v.i)); }
        else if (strcmp(cmd, "MUL") == 0) { Object b=pop(); Object a=pop(); push(make_int(a.v.i*b.v.i)); }
        else if (strcmp(cmd, "DIV") == 0) { Object b=pop(); Object a=pop(); push(make_int(a.v.i/b.v.i)); }
        else if (strcmp(cmd, "MOD") == 0) { Object b=pop(); Object a=pop(); push(make_int(a.v.i%b.v.i)); }
        else if (strcmp(cmd, "EQ") == 0) { Object b=pop(); Object a=pop(); push(make_int( (a.type==b.type && ((a.type==OBJ_INT && a.v.i==b.v.i) || (a.type==OBJ_STR && strcmp(a.v.s,b.v.s)==0))) ? 1:0 )); }
        else if (strcmp(cmd, "LT") == 0) { Object b=pop(); Object a=pop(); push(make_int(a.v.i < b.v.i ? 1:0)); }
        else if (strcmp(cmd, "JUMP") == 0) ip = find_label(arg);
        else if (strcmp(cmd, "JZERO") == 0) { if(pop().v.i == 0) ip = find_label(arg); }
        else if (strcmp(cmd, "CALL") == 0) call_method(arg);
        else if (strcmp(cmd, "GET") == 0) {
            Object key = pop();
            Object obj = pop();
            if(obj.type==OBJ_DICT) push(dict_get(obj.v.d, key.v.s));
            else if(obj.type==OBJ_LIST) push(obj.v.l->items[key.v.i]);
        }
        else if (strcmp(cmd, "SET") == 0) {
            Object key = pop();
            Object obj = pop();
            Object val = pop();
            if(obj.type==OBJ_DICT) dict_set(obj.v.d, key.v.s, val);
        }
    }
    return 0;
}
