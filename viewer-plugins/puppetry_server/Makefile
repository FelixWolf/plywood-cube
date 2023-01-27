#---------------------------------------------------------------------------------
.SUFFIXES:
#---------------------------------------------------------------------------------

TOPDIR ?= $(CURDIR)

ifeq ($(TARGETOS),)
TARGETOS	:= linux
endif

ifeq ($(TARGETOS), linux)
PREFIX		:=	
else ifeq ($(TARGETOS), windows)
PREFIX		:=	x86_64-w64-mingw32-
else
@echo Unknown target OS
@exit 0
endif


export CC	:=	$(PREFIX)gcc
export CXX	:=	$(PREFIX)g++
export AS	:=	$(PREFIX)as
export AR	:=	$(PREFIX)gcc-ar
export OBJCOPY	:=	$(PREFIX)objcopy
export STRIP	:=	$(PREFIX)strip
export NM	:=	$(PREFIX)gcc-nm
export RANLIB	:=	$(PREFIX)gcc-ranlib

#---------------------------------------------------------------------------------
# allow seeing compiler command lines with make V=1 (similar to autotools' silent)
#---------------------------------------------------------------------------------
ifeq ($(V),1)
    SILENTMSG := @true
    SILENTCMD :=
else
    SILENTMSG := @echo
    SILENTCMD := @
endif

#---------------------------------------------------------------------------------
# canned command sequence for binary data
#---------------------------------------------------------------------------------
define bin2o
	bin2s -a 4 -H `(echo $(<F) | tr . _)`.h $< | $(AS) -o $(<F).o
endef

#---------------------------------------------------------------------------------
# TARGET is the name of the output
# BUILD is the directory where object files & intermediate files will be placed
# SOURCES is a list of directories containing source code
# DATA is a list of directories containing data files
# INCLUDES is a list of directories containing header files
#---------------------------------------------------------------------------------
TARGET		:=	$(notdir $(CURDIR))
BUILD		:=	build
SOURCES		:=	source
DATA		:=
INCLUDES	:=	include

#---------------------------------------------------------------------------------
# options for code generation
#---------------------------------------------------------------------------------
ARCH	:=	-march=x86-64

CFLAGS	:=	-g -Wall -O2 $(ARCH)

CFLAGS	+=	$(INCLUDE)

CXXFLAGS	:= $(CFLAGS) -std=gnu++11

ASFLAGS	:=	-g $(ARCH)
LDFLAGS	=	-g $(ARCH) -Wl,-Map,$(notdir $*.map)


ifeq ($(TARGETOS), linux)
LIBS	:= -lSDL2 -lSDL2_net -lm
else ifeq ($(TARGETOS), windows)
LIBS	:= -lmingw32 -lSDL2main -lSDL2 -lSDL2_net -lws2_32 -static -static-libgcc -static-libstdc++ -Wl,-Bstatic -lstdc++ -lpthread -Wl,-Bdynamic -lm -mwindows
endif

#---------------------------------------------------------------------------------
# list of directories containing libraries, this must be the top level containing
# include and lib
#---------------------------------------------------------------------------------

ifeq ($(TARGETOS), linux)
LIBDIRS	:= /usr
else ifeq ($(TARGETOS), windows)
LIBDIRS	:= /usr/x86_64-w64-mingw32 /opt/mingw/x86_64-w64-mingw32/
endif

#---------------------------------------------------------------------------------
# no real need to edit anything past this point unless you need to add additional
# rules for different file extensions
#---------------------------------------------------------------------------------
ifneq ($(BUILD),$(notdir $(CURDIR)))
#---------------------------------------------------------------------------------

export OUTPUT	:=	$(CURDIR)/build/$(TARGET)
export TOPDIR	:=	$(CURDIR)

export VPATH	:=	$(foreach dir,$(SOURCES),$(CURDIR)/$(dir)) \
			$(foreach dir,$(DATA),$(CURDIR)/$(dir)) \
			$(foreach dir,$(GRAPHICS),$(CURDIR)/$(dir))

export DEPSDIR	:=	$(CURDIR)/$(BUILD)

CFILES		:=	$(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))
CPPFILES	:=	$(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.cpp)))
SFILES		:=	$(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.s)))
BINFILES	:=	$(foreach dir,$(DATA),$(notdir $(wildcard $(dir)/*.*)))

#---------------------------------------------------------------------------------
# use CXX for linking C++ projects, CC for standard C
#---------------------------------------------------------------------------------
ifeq ($(strip $(CPPFILES)),)
#---------------------------------------------------------------------------------
	export LD	:=	$(CC)
#---------------------------------------------------------------------------------
else
#---------------------------------------------------------------------------------
	export LD	:=	$(CXX)
#---------------------------------------------------------------------------------
endif
#---------------------------------------------------------------------------------

export OFILES_SOURCES 	:=	$(CPPFILES:.cpp=.o) $(CFILES:.c=.o) $(SFILES:.s=.o)

export OFILES_BIN	:=	$(addsuffix .o,$(BINFILES)) \

export OFILES := $(OFILES_BIN) $(OFILES_SOURCES)

export HFILES	:=	$(addsuffix .h,$(subst .,_,$(BINFILES)))

export INCLUDE	:=	$(foreach dir,$(INCLUDES),-I$(CURDIR)/$(dir)) \
			$(foreach dir,$(LIBDIRS),-I$(dir)/include) \
			-I$(CURDIR)/$(BUILD)

export LIBPATHS	:=	$(foreach dir,$(LIBDIRS),-L$(dir)/lib)


.PHONY: $(BUILD) clean all

all:	$(BUILD)

#---------------------------------------------------------------------------------
$(BUILD):
	@[ -d $@ ] || mkdir -p $@
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

#---------------------------------------------------------------------------------
clean:
	@echo clean ...
	@rm -fr $(BUILD) build/$(TARGET).x86_64 $(TARGET).i686 $(TARGET).exe


#---------------------------------------------------------------------------------
else

DEPENDS	:=	$(OFILES:.o=.d)


#---------------------------------------------------------------------------------
%.a:
#---------------------------------------------------------------------------------
	$(SILENTMSG) $(notdir $@)
	@rm -f $@
	$(SILENTCMD)$(AR) -rc $@ $^
#---------------------------------------------------------------------------------
%.o: %.cpp
	$(SILENTMSG) $(notdir $<)
	$(SILENTCMD)$(CXX) -MMD -MP -MF $(DEPSDIR)/$*.d $(CXXFLAGS) -c $< -o $@ $(ERROR_FILTER)

#---------------------------------------------------------------------------------
%.o: %.c
	$(SILENTMSG) $(notdir $<)
	$(SILENTCMD)$(CC) -MMD -MP -MF $(DEPSDIR)/$*.d $(CFLAGS) -c $< -o $@ $(ERROR_FILTER)

#---------------------------------------------------------------------------------
%.o: %.m
	$(SILENTMSG) $(notdir $<)
	$(SILENTCMD)$(CC) -MMD -MP -MF $(DEPSDIR)/$*.d $(OBJCFLAGS) -c $< -o $@ $(ERROR_FILTER)

#---------------------------------------------------------------------------------
%.o: %.s
	$(SILENTMSG) $(notdir $<)
	$(SILENTCMD)$(CC) -MMD -MP -MF $(DEPSDIR)/$*.d -x assembler-with-cpp $(ASFLAGS) -c $< -o $@ $(ERROR_FILTER)

#---------------------------------------------------------------------------------
%.o: %.S
	$(SILENTMSG) $(notdir $<)
	$(SILENTCMD)$(CC) -MMD -MP -MF $(DEPSDIR)/$*.d -x assembler-with-cpp $(ASFLAGS) -c $< -o $@ $(ERROR_FILTER)


%.x86_64:
	$(SILENTMSG) linking $(notdir $@)
	$(SILENTCMD)$(LD) $(LDFLAGS) $(OFILES) $(LIBPATHS) $(LIBS) -o $@
	$(SILENTCMD)$(NM) -CSn $@ > $(notdir $*.lst)

%.exe:
	$(SILENTMSG) linking $(notdir $@)
	$(SILENTCMD)$(LD) $(LDFLAGS) $(OFILES) $(LIBPATHS) $(LIBS) -o $@
	$(SILENTCMD)$(NM) -CSn $@ > $(notdir $*.lst)

#---------------------------------------------------------------------------------
# main targets
#---------------------------------------------------------------------------------
ifeq ($(TARGETOS), linux)
$(OUTPUT).x86_64: $(OUTPUT)
else ifeq ($(TARGETOS), windows)
$(OUTPUT).exe: $(OUTPUT)
endif

$(OFILES_SOURCES): $(HFILES)

$(OUTPUT): $(OFILES)

-include $(DEPENDS)

#---------------------------------------------------------------------------------------
endif
#---------------------------------------------------------------------------------------
