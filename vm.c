#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_STACK 1024
#define MAX_VARS 100
#define MAX_LABELS 100
#define MAX_LINES 2048
#define LINE_BUF_SIZE 256

// データ構造
typedef struct {
    char name[32];
    int value;
} Variable;

typedef struct {
    char name[32];
    int line_num;
} Label;

// グローバル状態
int stack[MAX_STACK];
int sp = 0; // stack pointer

Variable vars[MAX_VARS];
int var_count = 0;

Label labels[MAX_LABELS];
int label_count = 0;

char program[MAX_LINES][LINE_BUF_SIZE];
int prog_size = 0;

// スタック操作
void push(int val) {
    if (sp >= MAX_STACK) { fprintf(stderr, "Stack overflow\n"); exit(1); }
    stack[sp++] = val;
}

int pop() {
    if (sp <= 0) { fprintf(stderr, "Stack underflow\n"); exit(1); }
    return stack[--sp];
}

// 変数操作
int get_var(char *name) {
    for (int i = 0; i < var_count; i++) {
        if (strcmp(vars[i].name, name) == 0) return vars[i].value;
    }
    fprintf(stderr, "Undefined variable: %s\n", name);
    exit(1);
}

void set_var(char *name, int val) {
    for (int i = 0; i < var_count; i++) {
        if (strcmp(vars[i].name, name) == 0) {
            vars[i].value = val;
            return;
        }
    }
    // 新規作成
    if (var_count >= MAX_VARS) { fprintf(stderr, "Var limit reached\n"); exit(1); }
    strcpy(vars[var_count].name, name);
    vars[var_count].value = val;
    var_count++;
}

// ラベル検索
int find_label(char *name) {
    for (int i = 0; i < label_count; i++) {
        if (strcmp(labels[i].name, name) == 0) return labels[i].line_num;
    }
    fprintf(stderr, "Undefined label: %s\n", name);
    exit(1);
}

// 文字列が数値かどうか判定
int is_number(char *s) {
    if (*s == '-' || *s == '+') s++;
    if (!*s) return 0;
    while (*s) {
        if (!isdigit(*s)) return 0;
        s++;
    }
    return 1;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: ./vm <ir_file>\n");
        return 1;
    }

    FILE *fp = fopen(argv[1], "r");
    if (!fp) {
        perror("File open error");
        return 1;
    }

    // 1. 読み込み & ラベルスキャン
    char line[LINE_BUF_SIZE];
    while (fgets(line, sizeof(line), fp)) {
        // 改行削除
        line[strcspn(line, "\n")] = 0;
        if (strlen(line) == 0) continue;

        strcpy(program[prog_size], line);

        // ラベル定義を記録 (LABEL L1)
        if (strncmp(line, "LABEL ", 6) == 0) {
            char *label_name = line + 6;
            strcpy(labels[label_count].name, label_name);
            labels[label_count].line_num = prog_size;
            label_count++;
        }
        prog_size++;
    }
    fclose(fp);

    // 2. 実行ループ
    int ip = 0;
    while (ip < prog_size) {
        char buf[LINE_BUF_SIZE];
        strcpy(buf, program[ip]);
        
        char *cmd = strtok(buf, " ");
        char *arg = strtok(NULL, " ");

        ip++; // 基本は次へ

        if (strcmp(cmd, "LABEL") == 0) {
            // 何もしない
        } 
        else if (strcmp(cmd, "PUSH") == 0) {
            if (is_number(arg)) {
                push(atoi(arg));
            } else {
                // 【修正】文字列の場合もダミー値を積んでおく必要がある
                // そうしないと次のPRINTでpopしたときにunderflowする
                push(0);
            }
        }
        else if (strcmp(cmd, "STORE") == 0) { set_var(arg, pop()); }
        else if (strcmp(cmd, "LOAD") == 0) { push(get_var(arg)); }
        else if (strcmp(cmd, "ADD") == 0) { int b=pop(); int a=pop(); push(a+b); }
        else if (strcmp(cmd, "SUB") == 0) { int b=pop(); int a=pop(); push(a-b); }
        else if (strcmp(cmd, "MUL") == 0) { int b=pop(); int a=pop(); push(a*b); }
        else if (strcmp(cmd, "DIV") == 0) { int b=pop(); int a=pop(); push(a/b); }
        else if (strcmp(cmd, "MOD") == 0) { int b=pop(); int a=pop(); push(a%b); }
        else if (strcmp(cmd, "EQ") == 0) { int b=pop(); int a=pop(); push(a==b ? 1:0); }
        else if (strcmp(cmd, "LT") == 0) { int b=pop(); int a=pop(); push(a<b ? 1:0); }
        else if (strcmp(cmd, "JUMP") == 0) { ip = find_label(arg); }
        else if (strcmp(cmd, "JZERO") == 0) { if (pop() == 0) ip = find_label(arg); }
        else if (strcmp(cmd, "PRINT") == 0) {
            // 直前の命令を確認するハック
            char prev_buf[LINE_BUF_SIZE];
            // 安全策: ip-2 が範囲内か確認
            if (ip >= 2) {
                strcpy(prev_buf, program[ip-2]); 
                char *p_cmd = strtok(prev_buf, " ");
                char *p_arg = strtok(NULL, " ");
                
                if (p_cmd && strcmp(p_cmd, "PUSH") == 0 && !is_number(p_arg)) {
                    // 文字列リテラルのPUSHだった場合
                    pop(); // ダミー(0)を捨てる
                    printf("%s\n", p_arg);
                } else {
                    printf("%d\n", pop());
                }
            } else {
                 printf("%d\n", pop());
            }
        }
    }

    return 0;
}
