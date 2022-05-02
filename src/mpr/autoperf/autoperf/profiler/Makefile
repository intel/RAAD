$(info ###################################################################################)
$(info AutoPerf C and C++ libraries)
$(info ###################################################################################)
$(info Default uses)
$(info sudo apt-get install a2ps enscript build-essential python3 cscope -f --reinstall -y)
$(info sudo apt-get install libpapi-dev papi-examples papi-tools -f --reinstall -y)
$(info ###################################################################################)
$(info OR customize with)
$(info ###################################################################################)
$(info PAPI_LOCATION = ../../archieves/papi_5-5-1)
$(info ###################################################################################)

# Final and Scope Directories
BIN_DIR := bin
CSCOPE_DIR := scope
PERFPOINTLIB_DIR := lib

#Source Dir
INC_DIR := includes
SRC_DIR := src
C_SRCS = $(wildcard $(SRC_DIR)/*.c)
CPP_SRCS = $(wildcard $(SRC_DIR)/*.cpp)

# Static
S_DIR    :=  build_static
C_SOBJS_DIR = $(patsubst $(SRC_DIR)/%.c,$(S_DIR)/%.o,$(C_SRCS))
CPP_SOBJS_DIR = $(patsubst $(SRC_DIR)/%.cpp,$(S_DIR)/%.o,$(CPP_SRCS))

# Dynamic
D_DIR    :=  build_dynamic
C_DOBJS_DIR = $(patsubst $(SRC_DIR)/%.c,$(D_DIR)/%.o,$(C_SRCS))
CPP_DOBJS_DIR = $(patsubst $(SRC_DIR)/%.cpp,$(D_DIR)/%.o,$(CPP_SRCS))

CC = g++
LD = $(CC)
CFLAGS = -v -g -Wall -Werror -Wno-endif-labels -fno-omit-frame-pointer -O0 -march=native -fsplit-stack -m64 -ffloat-store -pedantic -I $(INC_DIR)
# CFLAGS += -DPERF_EVENT
LDFLAGS :=  -lpapi -lpthread -L$(D_DIR) -L$(S_DIR)
LDLIBS  :=  -l$(...)

NAME                :=  libperfpoint
TARGET_NAME_DYNAMIC :=$(NAME).so
TARGET_DYNAMIC      := $(D_DIR)/$(TARGET_NAME_DYNAMIC)
TARGET_NAME_STATIC  := $(NAME).a
TARGET_STATIC       := $(S_DIR)/$(TARGET_NAME_STATIC)

all: clean libbuild_dynamic libbuild_static CSCOPE cpbin_dynamic cpbin_static perfpointdir
# Create Directory
$(D_DIR) $(S_DIR) $(BIN_DIR) $(PERFPOINTLIB_DIR) $(CSCOPE_DIR):
	$(info 1. ####################)
	$(info && make directory: $@)
	@mkdir -p $@

# Dynamic
libbuild_dynamic: $(D_DIR) $(TARGET_DYNAMIC)
	$(info ************************)
	$(info 2. *********************)
	$(info ************************)
	$(info ** Dynamic Library built)
$(TARGET_DYNAMIC): CFLAGS += -fPIC
$(TARGET_DYNAMIC): CFLAGS += -DPERF_EVENT
$(TARGET_DYNAMIC): LDFLAGS += -shared
$(TARGET_DYNAMIC): $(C_DOBJS_DIR) $(CPP_DOBJS_DIR)
	$(info 3. ####################)
	$(LD) $(LDFLAGS) $^ -o $@
	$(info ************************)

# $(CC) $(CFLAGS) -fpermissive -c $< -o $@
$(D_DIR)/%.o: $(SRC_DIR)/%.c | $(D_DIR)
	$(info 9. #####################)
	$(CC) $(CFLAGS) -c $< -o $@

# $(CC) $(CFLAGS) -fpermissive -c $< -o $@
$(D_DIR)/%.o: $(SRC_DIR)/%.cpp | $(D_DIR)
	$(info 10. #####################)
	$(CC) $(CFLAGS) -c $< -o $@

$(D_DIR)/%.o: $(SRC_DIR)/%.S | $(D_DIR)
	$(info 11. #####################)
	$(CC) $(CFLAGS) -c $< -o $@

# Static
libbuild_static: libbuild_dynamic $(S_DIR) $(TARGET_STATIC)
	$(info ************************)
	$(info 4. *********************)
	$(info ************************)
	$(info ** Static Library built)
$(TARGET_STATIC): $(C_DOBJS_DIR) $(CPP_DOBJS_DIR)
	$(info 5. *********************)
	$(AR) $(ARFLAGS) $@ $^
	$(info ************************)

# Objects
# $(S_DIR)/%.o: $(SRC_DIR)/%.c | $(S_DIR)
# 	$(info 6. #####################)
# 	$(CC) $(CFLAGS) -c $< -o $@

# $(S_DIR)/%.o: $(SRC_DIR)/%.cpp | $(S_DIR)
# 	$(info 7. ####################)
# 	$(CC) $(CFLAGS) -c $< -o $@

# $(S_DIR)/%.o: $(SRC_DIR)/%.S | $(S_DIR)
# 	$(info 8. #####################)
# 	$(CC) $(CFLAGS) -c $< -o $@

# Generate cscope database
# Generate a list of all source files starting from the current directory
# The -o means logical or
# find . -name "*.c" -o -name "*.cc" -o -name "*.cpp" -o -name "*.h" -o -name "*.hh" -o -name "*.hpp" > cscope.files
# -q build fast but larger database
# -R search symbols recursively
# -b build the database only, don't fire cscope
# -i file that contains list of file paths to be processed
# This will generate a few cscope.* files
# cscope -q -R -b -i cscope.files
# Temporary files, remove them
# rm -f cscope.files cscope.in.out cscope.po.out
CSCOPE: $(S_DIR) $(D_DIR) $(CSCOPE_DIR)
	$(info 12. #####################)
	touch $(CSCOPE_DIR)/cscope.files
	find -L $(SRC_DIR) -name "*.c" -o -name "*.cc" -o -name "*.cpp" -o -name "*.h" -o -name "*.hh" -o -name "*.hpp" > $(CSCOPE_DIR)/cscope.files
	find -L $(INC_DIR) -name "*.c" -o -name "*.cc" -o -name "*.cpp" -o -name "*.h" -o -name "*.hh" -o -name "*.hpp" >> $(CSCOPE_DIR)/cscope.files
	cscope -R -b -q -k
	mv cscope.in.out $(CSCOPE_DIR)/cscope.in.out
	mv cscope.out $(CSCOPE_DIR)/cscope.out
	mv cscope.po.out $(CSCOPE_DIR)/cscope.po.out

cpbin_dynamic: $(BIN_DIR) libbuild_dynamic
	$(info 13. ####################)
	cp $(TARGET_DYNAMIC) $(BIN_DIR)/$(TARGET_NAME_DYNAMIC)

cpbin_static: $(BIN_DIR) libbuild_static
	$(info 14. ####################)
	cp $(TARGET_STATIC) $(BIN_DIR)/$(TARGET_NAME_STATIC)

clean:
	$(info 15. #####################)
	rm -f *.o *.so *.a *.files *.out
	rm -rf $(OBJ_DIR) $(D_DIR) $(S_DIR) $(BIN_DIR) $(CSCOPE_DIR)

perfpointdir: $(PERFPOINTLIB_DIR) libbuild_dynamic libbuild_static
	$(info 16. ####################)
	cp $(TARGET_DYNAMIC) $(PERFPOINTLIB_DIR)/$(TARGET_NAME_DYNAMIC)
	cp $(TARGET_STATIC) $(PERFPOINTLIB_DIR)/$(TARGET_NAME_STATIC)
	cp $(INC_DIR)/perfpoint.h $(PERFPOINTLIB_DIR)/perfpoint.h
