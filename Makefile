ifeq ($(OS), Windows_NT)
	OUT = swami.exe
	RM = del /Q
else
	OUT = swami
	RM = rm -f
endif

SW = ./swami.bat
SWFLAGS = -backend "clang" -b "-target x86_64-w64-mingw32"

swami: src/swami.sw
	$(SW) $(SWFLAGS) src/swami.sw -o $(OUT)

clean:
	$(RM) $(OUT)
