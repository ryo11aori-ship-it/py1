#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_STACK 2048
#define MAX_VARS 512
#define MAX_LABELS 512
#define MAX_LINES 4096
#define LINE_BUF_SIZE 1024

// --- Type System ---
typedef enum {
    OBJ_INT,
    OBJ_STR
} ObjType;

typedef struct {
    ObjType type;
    union {
        int i;
        char *s;
    } v;
} Object;

// --- Data Structures ---
Object stack[MAX_STACK];
int sp = 0;

typedef struct {
    char name[32];
    Object val;
} Variable;
Variable vars[MAX_VARS];
int var_count = 0;

typedef struct {
    char name[32];
    int line_num;
} Label;
Label labels[MAX_LABELS];
int label_count = 0;

char program[MAX_LINES][LINE_BUF_SIZE];
int prog_size = 0;

// --- Helpers ---
void panic(const char *msg) {
    fprintf(stderr, "Panic: %s\n", msg);
    exit(1);
}

Object make_int(int v) {
    Object o; o.type = OBJ_INT; o.v.i = v; return o;
}

Object make_str(const char *s) {
    Object o; o.type = OBJ_STR;
    o.v.s = strdup(s); // Simple heap allocation
    return o;
}

// --- Stack Ops ---
void push(Object obj) {
    if (sp >= MAX_STACK) panic("Stack overflow");
    stack[sp++] = obj;
}

Object pop() {
    if (sp <= 0) panic("Stack underflow");
    return stack[--sp];
}

// --- Variable Ops ---
Object get_var(char *name) {
    for (int i = 0; i < var_count; i++) {
        if (strcmp(vars[i].name, name) == 0) return vars[i].val;
    }
    // Undefined var returns INT 0 (or error in strict mode)
    return make_int(0); 
}

void set_var(char *name, Object val) {
    for (int i = 0; i < var_count; i++) {
        if (strcmp(vars[i].name, name) == 0) {
            vars[i].val = val;
            return;
        }
    }
    if (var_count >= MAX_VARS) panic("Var limit reached");
    strcpy(vars[var_count].name, name);
    vars[var_count].val = val;
    var_count++;
}

// --- Label Ops ---
int find_label(char *name) {
    for (int i = 0; i < label_count; i++) {
        if (strcmp(labels[i].name, name) == 0) return labels[i].line_num;
    }
    panic("Undefined label");
    return -1;
}

// --- Parser Helper ---
int is_number(char *s) {
    if (*s == '-' || *s == '+') s++;
    if (!*s) return 0;
    while (*s) {
        if (!isdigit(*s)) return 0;
        s++;
    }
    return 1;
}

// --- VM Main ---
int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: ./vm <ir_file>\n");
        return 1;
    }

    FILE *fp = fopen(argv[1], "r");
    if (!fp) { perror("File open error"); return 1; }

    // 1. Load Program
    char line[LINE_BUF_SIZE];
    while (fgets(line, sizeof(line), fp)) {
        line[strcspn(line, "\n")] = 0;
        if (strlen(line) == 0) continue;
        
        strcpy(program[prog_size], line);

        if (strncmp(line, "LABEL ", 6) == 0) {
            char *label_name = line + 6;
            strcpy(labels[label_count].name, label_name);
            labels[label_count].line_num = prog_size;
            label_count++;
        }
        prog_size++;
    }
    fclose(fp);

    // 2. Execution
    int ip = 0;
    while (ip < prog_size) {
        char buf[LINE_BUF_SIZE];
        strcpy(buf, program[ip]);
        
        // Split command and argument (Handling spaces in strings is rudimentary)
        char *cmd = strtok(buf, " ");
        char *arg = strtok(NULL, ""); // Get the rest
        if (arg) {
            // Trim leading spaces from arg
            while(*arg == ' ') arg++;
        }

        ip++;

        if (!cmd || strcmp(cmd, "LABEL") == 0) {
            // No-op
        }
        else if (strcmp(cmd, "PUSH") == 0) {
            if (arg) {
                if (is_number(arg)) {
                    push(make_int(atoi(arg)));
                } else {
                    // String literal handling
                    // If arg is just text, treat as string
                    push(make_str(arg));
                }
            } else {
                push(make_int(0)); // Empty PUSH
            }
        }
        else if (strcmp(cmd, "STORE") == 0) { set_var(arg, pop()); }
        else if (strcmp(cmd, "LOAD") == 0) { push(get_var(arg)); }
        else if (strcmp(cmd, "PRINT") == 0) {
            Object o = pop();
            if (o.type == OBJ_INT) printf("%d\n", o.v.i);
            else if (o.type == OBJ_STR) printf("%s\n", o.v.s);
        }
        else if (strcmp(cmd, "ADD") == 0) {
            Object b = pop();
            Object a = pop();
            if (a.type == OBJ_INT && b.type == OBJ_INT) {
                push(make_int(a.v.i + b.v.i));
            } else {
                // String concatenation (Primitive implementation)
                char tmp[1024];
                const char *sa = (a.type == OBJ_STR) ? a.v.s : "TODO_CONV"; // Int->Str conv needed later
                const char *sb = (b.type == OBJ_STR) ? b.v.s : "TODO_CONV";
                snprintf(tmp, sizeof(tmp), "%s%s", sa, sb);
                push(make_str(tmp));
            }
        }
        else if (strcmp(cmd, "SUB") == 0) {
            Object b = pop(); Object a = pop();
            if (a.type == OBJ_INT && b.type == OBJ_INT) push(make_int(a.v.i - b.v.i));
            else panic("Type error in SUB");
        }
        else if (strcmp(cmd, "MUL") == 0) {
            Object b = pop(); Object a = pop();
            if (a.type == OBJ_INT && b.type == OBJ_INT) push(make_int(a.v.i * b.v.i));
            else panic("Type error in MUL");
        }
        else if (strcmp(cmd, "DIV") == 0) {
             Object b = pop(); Object a = pop();
             if (b.v.i == 0) panic("Div by zero");
             push(make_int(a.v.i / b.v.i));
        }
        else if (strcmp(cmd, "MOD") == 0) {
             Object b = pop(); Object a = pop();
             push(make_int(a.v.i % b.v.i));
        }
        else if (strcmp(cmd, "EQ") == 0) {
            Object b = pop(); Object a = pop();
            int eq = 0;
            if (a.type != b.type) eq = 0;
            else if (a.type == OBJ_INT) eq = (a.v.i == b.v.i);
            else if (a.type == OBJ_STR) eq = (strcmp(a.v.s, b.v.s) == 0);
            push(make_int(eq ? 1 : 0));
        }
        else if (strcmp(cmd, "LT") == 0) {
            Object b = pop(); Object a = pop();
            if (a.type == OBJ_INT && b.type == OBJ_INT) push(make_int(a.v.i < b.v.i ? 1 : 0));
            else push(make_int(0));
        }
        else if (strcmp(cmd, "JUMP") == 0) { ip = find_label(arg); }
        else if (strcmp(cmd, "JZERO") == 0) {
            Object o = pop();
            if (o.type == OBJ_INT && o.v.i == 0) ip = find_label(arg);
        }
    }
    return 0;
}
