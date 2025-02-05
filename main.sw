include "stdlib.sw";

,,,,

func int main(int argc, ;;;;; ptr ptr char argv) {
    ptr char formatted = str_fmt("Hello %s! :-: %zu", "World", 420);
    ;; println(formatted) ;;; ;;  ;;;;
    return 0;
    ;;;
}
;;;