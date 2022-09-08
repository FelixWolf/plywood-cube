#include <string>
#include <iostream>
#include <ostream>

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdarg.h>
#include <math.h>
#include <assert.h>
#include <limits.h>
#include <time.h>
#include <unistd.h>

#include <SDL2/SDL.h>
#include <SDL2/SDL_net.h>

#define NK_INCLUDE_FIXED_TYPES
#define NK_INCLUDE_STANDARD_IO
#define NK_INCLUDE_STANDARD_VARARGS
#define NK_INCLUDE_DEFAULT_ALLOCATOR
#define NK_INCLUDE_VERTEX_BUFFER_OUTPUT
#define NK_INCLUDE_FONT_BAKING
#define NK_INCLUDE_DEFAULT_FONT
#define NK_IMPLEMENTATION
#define NK_SDL_RENDERER_IMPLEMENTATION

#include "nuklear.h"
#include "nuklear_sdl_renderer.h"


#define WINDOW_TITLE "Puppetry Server"
#define WINDOW_WIDTH 256
#define WINDOW_HEIGHT 512

#define MAX_CONNECTIONS 10

/* Native window implementation */
NK_API nk_bool
nk_begin_main_win(SDL_Window *window, SDL_Renderer *renderer,
    struct nk_context *ctx, const char *title,
    struct nk_rect bounds, nk_flags flags){
    nk_bool test = nk_begin(ctx, title, bounds, flags);
    if(test){
        //Check if we are dragging the title bar
        struct nk_window *win = ctx->current;
        /* window movement */
        struct nk_vec2 panel_padding = nk_panel_get_padding(&ctx->style, ctx->current->layout->type);
        
        nk_bool left_mouse_down;
        unsigned int left_mouse_clicked;
        int left_mouse_click_in_cursor;

        /* calculate draggable window space */
        struct nk_rect header;
        header.x = win->bounds.x;
        header.y = win->bounds.y;
        header.w = win->bounds.w;
        if (nk_panel_has_header(win->flags, title)) {
            header.h = ctx->style.font->height + 2.0f * ctx->style.window.header.padding.y;
            header.h += 2.0f * ctx->style.window.header.label_padding.y;
        } else header.h = panel_padding.y;

        /* window movement by dragging */
        left_mouse_down = ctx->input.mouse.buttons[NK_BUTTON_LEFT].down;
        left_mouse_clicked = ctx->input.mouse.buttons[NK_BUTTON_LEFT].clicked;
        left_mouse_click_in_cursor = nk_input_has_mouse_click_down_in_rect(&ctx->input,
            NK_BUTTON_LEFT, header, nk_true);
        if (left_mouse_down && left_mouse_click_in_cursor && !left_mouse_clicked) {
            int window_x, window_y;
            SDL_GetWindowPosition(window, &window_x, &window_y);
            window_x += ctx->input.mouse.delta.x;
            window_y += ctx->input.mouse.delta.y;
            ctx->input.mouse.pos.x -= ctx->input.mouse.delta.x;
            ctx->input.mouse.pos.y -= ctx->input.mouse.delta.y;
            ctx->input.mouse.prev.y -= ctx->input.mouse.delta.y;
            ctx->input.mouse.prev.y -= ctx->input.mouse.delta.y;
            ctx->style.cursor_active = ctx->style.cursors[NK_CURSOR_MOVE];
            SDL_SetWindowPosition(window, window_x, window_y);
        }
        SDL_SetWindowSize(window, win->bounds.w, win->bounds.h);
        return test;
    }
    return test;
}

static void setNkStyle(struct nk_context *ctx){
    struct nk_color table[NK_COLOR_COUNT];
    table[NK_COLOR_TEXT] = nk_rgba(210, 210, 210, 255);
    table[NK_COLOR_WINDOW] = nk_rgba(57, 67, 71, 255);
    table[NK_COLOR_HEADER] = nk_rgba(51, 51, 56, 255);
    table[NK_COLOR_BORDER] = nk_rgba(46, 46, 46, 255);
    table[NK_COLOR_BUTTON] = nk_rgba(48, 83, 111, 255);
    table[NK_COLOR_BUTTON_HOVER] = nk_rgba(58, 93, 121, 255);
    table[NK_COLOR_BUTTON_ACTIVE] = nk_rgba(63, 98, 126, 255);
    table[NK_COLOR_TOGGLE] = nk_rgba(50, 58, 61, 255);
    table[NK_COLOR_TOGGLE_HOVER] = nk_rgba(45, 53, 56, 255);
    table[NK_COLOR_TOGGLE_CURSOR] = nk_rgba(48, 83, 111, 255);
    table[NK_COLOR_SELECT] = nk_rgba(57, 67, 61, 255);
    table[NK_COLOR_SELECT_ACTIVE] = nk_rgba(48, 83, 111, 255);
    table[NK_COLOR_SLIDER] = nk_rgba(50, 58, 61, 255);
    table[NK_COLOR_SLIDER_CURSOR] = nk_rgba(48, 83, 111, 255);
    table[NK_COLOR_SLIDER_CURSOR_HOVER] = nk_rgba(53, 88, 116, 255);
    table[NK_COLOR_SLIDER_CURSOR_ACTIVE] = nk_rgba(58, 93, 121, 255);
    table[NK_COLOR_PROPERTY] = nk_rgba(50, 58, 61, 255);
    table[NK_COLOR_EDIT] = nk_rgba(50, 58, 61, 255);
    table[NK_COLOR_EDIT_CURSOR] = nk_rgba(210, 210, 210, 255);
    table[NK_COLOR_COMBO] = nk_rgba(50, 58, 61, 255);
    table[NK_COLOR_CHART] = nk_rgba(50, 58, 61, 255);
    table[NK_COLOR_CHART_COLOR] = nk_rgba(48, 83, 111, 255);
    table[NK_COLOR_CHART_COLOR_HIGHLIGHT] = nk_rgba(255, 0, 0, 255);
    table[NK_COLOR_SCROLLBAR] = nk_rgba(50, 58, 61, 255);
    table[NK_COLOR_SCROLLBAR_CURSOR] = nk_rgba(48, 83, 111, 255);
    table[NK_COLOR_SCROLLBAR_CURSOR_HOVER] = nk_rgba(53, 88, 116, 255);
    table[NK_COLOR_SCROLLBAR_CURSOR_ACTIVE] = nk_rgba(58, 93, 121, 255);
    table[NK_COLOR_TAB_HEADER] = nk_rgba(48, 83, 111, 255);
    nk_style_from_table(ctx, table);
}

template<typename... Args> std::string cprint(const char *f, Args... args){
    size_t sz;
    sz = snprintf(NULL, 0, f, args...);
    char buf[sz+1];
    snprintf(buf, sz+1, f, args...);
    std::string myString = buf;
    return myString;;
}

template<typename... Args> void doError(const char *f, Args... args){
    std::string result = cprint(f, args...);
    SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "ERROR",
        result.c_str(),
        NULL
    );
    exit(-1);
}

template<typename... Args> void doWarning(const char *f, Args... args){
    std::string result = cprint(f, args...);
    SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_WARNING, "WARNING",
        result.c_str(),
        NULL
    );
}

    
int viewerMsg;
int clientMsg;
int conns;

bool serverRunning = false;
int initMessageSize;
uint8_t *initMessage;

TCPsocket server_socket;
SDLNet_SocketSet socket_set;
TCPsocket sockets[MAX_CONNECTIONS];
void CloseSocket(int i){
    conns--;
    if(SDLNet_TCP_DelSocket(socket_set, sockets[i]) == -1) {
        doWarning("ER: SDLNet_TCP_DelSocket: %sn", SDLNet_GetError());
    }
    SDLNet_TCP_Close(sockets[i]);
    sockets[i] = NULL;
}

int main(int argc, char *argv[]){
    /* Platform */
    int running = 1;
    float font_scale = 1;

    /* SDL setup */
    SDL_SetHint(SDL_HINT_VIDEO_HIGHDPI_DISABLED, "0");
    SDL_Init(SDL_INIT_VIDEO|SDL_INIT_TIMER|SDL_INIT_EVENTS);
    
    if(SDLNet_Init() == -1) {
        doError("ER: SDLNet_Init: %sn", SDLNet_GetError());
    }
    
    SDL_Window *win = SDL_CreateWindow(WINDOW_TITLE,
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        WINDOW_WIDTH, WINDOW_HEIGHT,
        SDL_WINDOW_SHOWN|SDL_WINDOW_ALLOW_HIGHDPI|SDL_WINDOW_BORDERLESS);

    if (win == NULL) {
        doError("Error SDL_CreateWindow %s", SDL_GetError());
    }

    int flags = SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC;

    SDL_Renderer *renderer = SDL_CreateRenderer(win, -1, flags);

    if (renderer == NULL) {
        doError("Error SDL_CreateRenderer %s", SDL_GetError());
    }

    /* scale the renderer output for High-DPI displays */
    {
        int render_w, render_h;
        int window_w, window_h;
        float scale_x, scale_y;
        SDL_GetRendererOutputSize(renderer, &render_w, &render_h);
        SDL_GetWindowSize(win, &window_w, &window_h);
        scale_x = (float)(render_w) / (float)(window_w);
        scale_y = (float)(render_h) / (float)(window_h);
        SDL_RenderSetScale(renderer, scale_x, scale_y);
        font_scale = scale_y;
    }

    /* GUI */
    struct nk_context *ctx = nk_sdl_init(win, renderer);
    setNkStyle(ctx);
    /* Load Fonts: if none of these are loaded a default font will be used  */
    /* Load Cursor: if you uncomment cursor loading please hide the cursor */
    {
        struct nk_font_atlas *atlas;
        struct nk_font_config config = nk_font_config(0);
        struct nk_font *font;

        /* set up the font atlas and add desired font; note that font sizes are
         * multiplied by font_scale to produce better results at higher DPIs */
        nk_sdl_font_stash_begin(&atlas);
        font = nk_font_atlas_add_default(atlas, 13 * font_scale, &config);
        nk_sdl_font_stash_end();

        /* this hack makes the font appear to be scaled down to the desired
         * size and is only necessary when font_scale > 1 */
        font->handle.height /= font_scale;
        nk_style_set_font(ctx, &font->handle);
    }
    
    fd_set fds;
    
    while (running){
        /* TCP Socket */
        if(serverRunning){
            if(SDLNet_CheckSockets(socket_set, 10) > 0){
                if(SDLNet_SocketReady(server_socket)) {
                    int i = 0;
                    for(; i<MAX_CONNECTIONS; i++){
                        if(sockets[i] == NULL) break;
                    }
                    
                    if(sockets[i]) {
                        CloseSocket(i);
                    }
                
                    sockets[i] = SDLNet_TCP_Accept(server_socket);
                    if(sockets[i] == NULL) return 0;
                    
                    if(SDLNet_TCP_AddSocket(socket_set, sockets[i]) == -1) {
                        doWarning("ER: SDLNet_TCP_AddSocket: %sn", SDLNet_GetError());
                    }
                    conns++;
                    if(initMessage != NULL){
                        int nSent = SDLNet_TCP_Send(sockets[i], initMessage, initMessageSize);
                        if(nSent < initMessageSize) {
                            doWarning("ER: SDLNet_TCP_Send: %sn", SDLNet_GetError());
                            CloseSocket(i);
                        }
                    }
                }
                for(int i=0; i<MAX_CONNECTIONS; i++) {
                    if(sockets[i] == NULL) continue;
                    if(!SDLNet_SocketReady(sockets[i])) continue;
                    
                    int packetSize = 0;
                    while(true){
                        uint8_t data[1];
                        int dlen = SDLNet_TCP_Recv(sockets[i], data, 1);
                    
                        if(dlen <= 0){
                            const char* err = SDLNet_GetError();
                            if(strlen(err) != 0){
                                doError("ER: SDLNet_TCP_Recv: %sn", err);
                            }
                            CloseSocket(i);
                            packetSize = -1;
                            break;
                        }
                        if(data[0] == ':'){
                            break;
                        }else if(data[0] >= '0' && data[0] <= '9'){
                            packetSize *= 10;
                            packetSize += (int)(data[0] - '0');
                        }else{
                            //Invalid data, discard and disconnect
                            CloseSocket(i);
                            packetSize = -1;
                            break;
                        }
                    }
                    if(packetSize == -1){
                        //Client disconnected
                        break;
                    }
                    if(packetSize > 0xFFFF){
                        //Mega packet, probably malformed.
                            CloseSocket(i);
                        break;
                    }
                    
                    uint8_t data[packetSize];
                    uint8_t *dataPointer = (uint8_t*)data;
                    int remaining = packetSize;
                    while(true){
                        if(remaining <= 0)
                            break;
                        int dlen = SDLNet_TCP_Recv(sockets[i], dataPointer, remaining);
                        
                        if(dlen < 0){
                            const char* err = SDLNet_GetError();
                            if(strlen(err) != 0){
                                doError("ER: SDLNet_TCP_Recv: %sn", err);
                            }
                            CloseSocket(i);
                            break;
                        }
                        dataPointer += dlen;
                        remaining -= dlen;
                    }
                    if(remaining == 0){
                        clientMsg++;
                        
                        std::string s = std::to_string(packetSize);
                        int mSize = s.size()+packetSize+1;
                        uint8_t _msg[mSize];
                        uint8_t *msg = _msg;
                        memcpy(msg, s.c_str(), s.size()); msg += s.size();
                        msg[0] = ':'; msg++;
                        memcpy(msg, data, packetSize);
                        write(STDOUT_FILENO, _msg, mSize);
                    }
                }
            }
        }
        
        /* stdin socket */
        FD_ZERO(&fds);
        FD_SET(STDIN_FILENO, &fds);
        struct timeval timeout = {0, 10000};
        int result = select(STDIN_FILENO+1, &fds, NULL, NULL, &timeout);
        if (result == -1 && errno != EINTR)
        {
            doError("Error in select: %i", strerror(errno));
            break;
        }
        else if (result == -1 && errno == EINTR)
        {
            //we've received and interrupt - handle this
        }
        else
        {
            if (FD_ISSET(STDIN_FILENO, &fds))
            {
                int packetSize = 0;
                while(true){
                    uint8_t data[1];
                    int dlen = read(STDIN_FILENO, data, 1);
                
                    if(dlen <= 0){
                        doWarning("Viewer socket closed!?");
                        packetSize = -1;
                        break;
                    }
                    if(data[0] == ':'){
                        break;
                    }else if(data[0] >= '0' && data[0] <= '9'){
                        packetSize *= 10;
                        packetSize += (int)(data[0] - '0');
                    }else{
                        doWarning("Viewer sent invalid data!");
                        packetSize = -1;
                        break;
                    }
                }
                if(packetSize == -1){
                    //Client disconnected
                    break;
                }
                if(packetSize > 0xFFFF){
                    //Mega packet, probably malformed.
                    doWarning("Viewer sent mega data!");
                    break;
                }
                
                uint8_t data[packetSize];
                uint8_t *dataPointer = (uint8_t*)data;
                int remaining = packetSize;
                while(true){
                    if(remaining <= 0)
                        break;
                    int dlen = read(STDIN_FILENO, dataPointer, remaining);
                    
                    if(dlen < 0){
                        doWarning("Viewer socket closed!?");
                        break;
                    }
                    dataPointer += dlen;
                    remaining -= dlen;
                }
                if(remaining == 0){
                    std::string s = std::to_string(packetSize);
                    int mSize = s.size()+packetSize+1;
                    uint8_t _msg[mSize];
                    uint8_t *msg = _msg;
                    memcpy(msg, s.c_str(), s.size()); msg += s.size();
                    msg[0] = ':'; msg++;
                    memcpy(msg, data, packetSize);
                    if(initMessage == NULL){
                        initMessage = (uint8_t *)malloc(mSize);
                        initMessageSize = mSize;
                        memcpy(initMessage, _msg, initMessageSize);
                    }
                    viewerMsg++;
                    if(serverRunning){
                        for(int i=0; i<MAX_CONNECTIONS; i++) {
                            if(sockets[i] == NULL) continue;
                            int nSent = SDLNet_TCP_Send(sockets[i], _msg, mSize);
                            if(nSent < mSize) {
                                doWarning("ER: SDLNet_TCP_Send: %sn", SDLNet_GetError());
                                CloseSocket(i);
                            }
                        }
                    }
                }
            }
        }
        
        /* Input */
        SDL_Event evt;
        nk_input_begin(ctx);
        while (SDL_PollEvent(&evt)) {
            if (evt.type == SDL_QUIT) goto cleanup;
            nk_sdl_handle_event(&evt);
        }
        nk_input_end(ctx);
        
        int render_w, render_h;
        SDL_GetWindowSize(win, &render_w, &render_h);
        /* GUI */
        if (nk_begin_main_win(win, renderer, ctx, WINDOW_TITLE, nk_rect(0, 0, render_w, render_h),
            NK_WINDOW_BORDER|NK_WINDOW_CLOSABLE|
            NK_WINDOW_MINIMIZABLE|NK_WINDOW_TITLE|NK_WINDOW_SCALABLE))
        {
            
            nk_layout_row_dynamic(ctx, 30, 1);
            nk_label_wrap(ctx,
            "This is a prototype puppetry server for a prototype viewer.");
            nk_label_wrap(ctx,
            "Protocol is subject to change, as such be sure to make sure");
            nk_label_wrap(ctx,
            "that you are running the latest version of this!");
            nk_layout_row_dynamic(ctx, 30, 1);
            nk_label_wrap(ctx,"");
            nk_layout_row_dynamic(ctx, 10, 2);
            nk_label(ctx, "Connections:", NK_TEXT_LEFT);
            nk_label(ctx, std::to_string(conns).c_str(), NK_TEXT_LEFT);
            nk_label(ctx, "Viewer commands:", NK_TEXT_LEFT);
            nk_label(ctx, std::to_string(viewerMsg).c_str(), NK_TEXT_LEFT);
            nk_label(ctx, "Client commands:", NK_TEXT_LEFT);
            nk_label(ctx, std::to_string(clientMsg).c_str(), NK_TEXT_LEFT);
            nk_layout_row_dynamic(ctx, 30, 1);
            nk_label_wrap(ctx,"");
            nk_layout_row_dynamic(ctx, 0, 1);
            static int property_allow_external_connections = nk_false;
            nk_checkbox_label(ctx, "Allow external connections", &property_allow_external_connections);
            static int property_port = 5000;
            nk_property_int(ctx, "Int:", 1025, &property_port, 65535, 1, 1);
            if(serverRunning == false){
                if (nk_button_label(ctx, "Start Server")){
                    IPaddress ip;
                    if(SDLNet_ResolveHost(&ip, NULL, property_port) == -1) {
                        doWarning("ER: SDLNet_ResolveHost: %sn", SDLNet_GetError());
                    }else{
                        server_socket = SDLNet_TCP_Open(&ip);
                        if(server_socket == NULL) {
                            doWarning("ER: SDLNet_TCP_Open: %sn", SDLNet_GetError());
                        }else{
                            socket_set = SDLNet_AllocSocketSet(MAX_CONNECTIONS+1);
                            if(socket_set == NULL) {
                                doWarning("ER: SDLNet_AllocSocketSet: %sn", SDLNet_GetError());
                            }else{
                                if(SDLNet_TCP_AddSocket(socket_set, server_socket) == -1) {
                                    doWarning("ER: SDLNet_TCP_AddSocket: %sn", SDLNet_GetError());
                                }else{
                                    serverRunning = true;
                                }
                            }
                        }
                    }
                }
            }else{
                if (nk_button_label(ctx, "Stop Server")){
                    if(SDLNet_TCP_DelSocket(socket_set, server_socket) == -1) {
                        doWarning("ER: SDLNet_TCP_DelSocket: %sn", SDLNet_GetError());
                    }else{
                        SDLNet_TCP_Close(server_socket);
                        for(int i=0; i<MAX_CONNECTIONS; ++i) {
                            if(sockets[i] == NULL) continue;
                            CloseSocket(i);
                            sockets[i] = NULL;
                        }
                        serverRunning = false;
                    }
                }
            }

        }
        nk_end(ctx);
        if(nk_window_is_hidden(ctx, WINDOW_TITLE)){
            running = false;
        }
        
        if(nk_window_is_collapsed(ctx, WINDOW_TITLE)){
            SDL_MinimizeWindow(win);
            nk_window_collapse(ctx, WINDOW_TITLE, NK_MAXIMIZED);
        }
        
        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0);
        SDL_RenderClear(renderer);
        nk_sdl_render(NK_ANTI_ALIASING_OFF);

        SDL_RenderPresent(renderer);
        SDL_ShowCursor(true);
    }

cleanup:
    nk_sdl_shutdown();
    SDLNet_Quit();
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(win);
    SDL_Quit();
    return 0;
}