goog.provide('dandy');
goog.require('cljs.core');
goog.require('dandy.levels');
goog.require('dandy.assets');
goog.require('dandy.assets');
goog.require('dandy.levels');
dandy.levelWidth = 60;
dandy.levelHeight = 30;
dandy.tileWidth = 16;
dandy.tileHeight = 16;
dandy.tileScale = 2;
dandy.kSpace = 0;
dandy.kWall = 1;
dandy.kDoor = 2;
dandy.kUp = 3;
dandy.kDown = 4;
dandy.kKey = 5;
dandy.kFood = 6;
dandy.kMoney = 7;
dandy.kBomb = 8;
dandy.kMonster1 = 9;
dandy.kMonster2 = 10;
dandy.kMonster3 = 11;
dandy.kHeart = 12;
dandy.kGenerator1 = 13;
dandy.kGenerator2 = 14;
dandy.kGenerator3 = 15;
dandy.kArrow = 16;
dandy.kPlayer1 = (dandy.kArrow + 8);
dandy.kDirToDeltaX = cljs.core.PersistentVector.fromArray([0,1,1,1,0,-1,-1,-1], true);
dandy.kDirToDeltaY = cljs.core.PersistentVector.fromArray([-1,-1,0,1,1,1,0,-1], true);
dandy.PLAYER_SPAWN_DIRS = cljs.core.PersistentVector.fromArray([0,2,4,6], true);
dandy.kButtonLeft = 1;
dandy.kButtonRight = 2;
dandy.kButtonUp = 4;
dandy.kButtonDown = 8;
dandy.kButtonFire = 16;
dandy.kButtonBomb = 32;
dandy.kNeighborOffsets = cljs.core.PersistentVector.fromArray([cljs.core.PersistentVector.fromArray([-1,-1], true),cljs.core.PersistentVector.fromArray([0,-1], true),cljs.core.PersistentVector.fromArray([1,-1], true),cljs.core.PersistentVector.fromArray([-1,0], true),cljs.core.PersistentVector.fromArray([1,0], true),cljs.core.PersistentVector.fromArray([-1,1], true),cljs.core.PersistentVector.fromArray([0,1], true),cljs.core.PersistentVector.fromArray([1,1], true)], true);
dandy.kKeyboardInputConfigs = cljs.core.PersistentVector.fromArray([cljs.core.PersistentArrayMap.fromArray(["\uFDD0:up","ArrowUp","\uFDD0:down","ArrowDown","\uFDD0:left","ArrowLeft","\uFDD0:right","ArrowRight","\uFDD0:fire","Space","\uFDD0:bomb","KeyB"], true),cljs.core.PersistentArrayMap.fromArray(["\uFDD0:up","KeyW","\uFDD0:down","KeyS","\uFDD0:left","KeyA","\uFDD0:right","KeyD","\uFDD0:fire","KeyF","\uFDD0:bomb","KeyG"], true)], true);
dandy.abs = (function abs(v){
if((v < 0))
{return (- v);
} else
{return v;
}
});
dandy.map_get = (function map_get(state_map,x,y){
if((function (){var and__3941__auto__ = (x >= 0);
if(and__3941__auto__)
{var and__3941__auto____$1 = (x < 60);
if(and__3941__auto____$1)
{var and__3941__auto____$2 = (y >= 0);
if(and__3941__auto____$2)
{return (y < 30);
} else
{return and__3941__auto____$2;
}
} else
{return and__3941__auto____$1;
}
} else
{return and__3941__auto__;
}
})())
{return cljs.core.nth.call(null,state_map,(x + (y * 60)));
} else
{return 1;
}
});
dandy.map_set = (function map_set(state_map,x,y,val){
if((function (){var and__3941__auto__ = (x >= 0);
if(and__3941__auto__)
{var and__3941__auto____$1 = (x < 60);
if(and__3941__auto____$1)
{var and__3941__auto____$2 = (y >= 0);
if(and__3941__auto____$2)
{return (y < 30);
} else
{return and__3941__auto____$2;
}
} else
{return and__3941__auto____$1;
}
} else
{return and__3941__auto__;
}
})())
{return cljs.core.assoc.call(null,state_map,(x + (y * 60)),val);
} else
{return state_map;
}
});
dandy.map_set_transient_BANG_ = (function map_set_transient_BANG_(state_map,x,y,val){
if((function (){var and__3941__auto__ = (x >= 0);
if(and__3941__auto__)
{var and__3941__auto____$1 = (x < 60);
if(and__3941__auto____$1)
{var and__3941__auto____$2 = (y >= 0);
if(and__3941__auto____$2)
{return (y < 30);
} else
{return and__3941__auto____$2;
}
} else
{return and__3941__auto____$1;
}
} else
{return and__3941__auto__;
}
})())
{return cljs.core.assoc_BANG_.call(null,state_map,(x + (y * 60)),val);
} else
{return state_map;
}
});
dandy.map_find = (function map_find(state_map,item){
return cljs.core.first.call(null,cljs.core.keep_indexed.call(null,(function (idx,val){
if(cljs.core._EQ_.call(null,val,item))
{return cljs.core.PersistentVector.fromArray([cljs.core.mod.call(null,idx,60),cljs.core.quot.call(null,idx,60)], true);
} else
{return null;
}
}),state_map));
});
dandy.load_level_map = (function load_level_map(level_idx){
return cljs.core.nth.call(null,dandy.levels.levels,level_idx);
});
dandy.align_even = (function align_even(val){
return (val & -2);
});
dandy.calculate_target_cog = (function calculate_target_cog(players){
var active_alive = cljs.core.filter.call(null,(function (p){
var and__3941__auto__ = (new cljs.core.Keyword("\uFDD0:active")).call(null,p);
if(cljs.core.truth_(and__3941__auto__))
{var and__3941__auto____$1 = (new cljs.core.Keyword("\uFDD0:alive")).call(null,p);
if(cljs.core.truth_(and__3941__auto____$1))
{return cljs.core.not.call(null,(new cljs.core.Keyword("\uFDD0:escaped")).call(null,p));
} else
{return and__3941__auto____$1;
}
} else
{return and__3941__auto__;
}
}),players);
var cnt = cljs.core.count.call(null,active_alive);
if((cnt > 0))
{var sum_x = cljs.core.reduce.call(null,cljs.core._PLUS_,cljs.core.map.call(null,(function (p){
return ((new cljs.core.Keyword("\uFDD0:x")).call(null,p) * 16);
}),active_alive));
var sum_y = cljs.core.reduce.call(null,cljs.core._PLUS_,cljs.core.map.call(null,((function (sum_x){
return (function (p){
return ((new cljs.core.Keyword("\uFDD0:y")).call(null,p) * 16);
});})(sum_x))
,active_alive));
return cljs.core.PersistentVector.fromArray([(cljs.core.quot.call(null,sum_x,cnt) + 8),(cljs.core.quot.call(null,sum_y,cnt) + 8)], true);
} else
{return cljs.core.PersistentVector.fromArray([((10 * 16) + 8),((5 * 16) + 8)], true);
}
});
dandy.get_camera_offsets = (function get_camera_offsets(camera){
var screen_w = 320.0;
var screen_h = 160.0;
var map_w = (60 * 16.0);
var map_h = (30 * 16.0);
var offset_x = ((- (new cljs.core.Keyword("\uFDD0:x")).call(null,camera)) + (screen_w / 2.0));
var offset_y = ((- (new cljs.core.Keyword("\uFDD0:y")).call(null,camera)) + (screen_h / 2.0));
var clamped_x = (((- (map_w - screen_w)) > ((0.0 < offset_x) ? 0.0 : offset_x)) ? (- (map_w - screen_w)) : ((0.0 < offset_x) ? 0.0 : offset_x));
var clamped_y = (((- (map_h - screen_h)) > ((0.0 < offset_y) ? 0.0 : offset_y)) ? (- (map_h - screen_h)) : ((0.0 < offset_y) ? 0.0 : offset_y));
return [clamped_x,clamped_y];
});
dandy.get_active_rect = (function get_active_rect(camera){
var offsets = dandy.get_camera_offsets.call(null,camera);
var offset_x = (offsets[0]);
var offset_y = (offsets[1]);
var left = (Math.floor(((- offset_x) / 16.0)) | 0);
var right = (Math.floor(((((- offset_x) + 320.0) + 15.0) / 16.0)) | 0);
var top = (Math.floor(((- offset_y) / 16.0)) | 0);
var bottom = (Math.floor(((((- offset_y) + 160.0) + 15.0) / 16.0)) | 0);
var left__$1 = ((0 > ((60 < left) ? 60 : left)) ? 0 : ((60 < left) ? 60 : left));
var right__$1 = ((0 > ((60 < right) ? 60 : right)) ? 0 : ((60 < right) ? 60 : right));
var top__$1 = ((0 > ((30 < top) ? 30 : top)) ? 0 : ((30 < top) ? 30 : top));
var bottom__$1 = ((0 > ((30 < bottom) ? 30 : bottom)) ? 0 : ((30 < bottom) ? 30 : bottom));
return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:left",left__$1,"\uFDD0:top",top__$1,"\uFDD0:width",(right__$1 - left__$1),"\uFDD0:height",(bottom__$1 - top__$1)], true);
});
dandy.update_camera = (function update_camera(camera,players){
var vec__3477 = dandy.calculate_target_cog.call(null,players);
var tx = cljs.core.nth.call(null,vec__3477,0,null);
var ty = cljs.core.nth.call(null,vec__3477,1,null);
var max_rate = (16.0 / 4.0);
var dx = (tx - (new cljs.core.Keyword("\uFDD0:x")).call(null,camera));
var dy = (ty - (new cljs.core.Keyword("\uFDD0:y")).call(null,camera));
var clamp = ((function (vec__3477,tx,ty,max_rate,dx,dy){
return (function (v,r){
return (((- r) > ((r < v) ? r : v)) ? (- r) : ((r < v) ? r : v));
});})(vec__3477,tx,ty,max_rate,dx,dy))
;
var cdx = clamp.call(null,dx,max_rate);
var cdy = clamp.call(null,dy,max_rate);
return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:x",((new cljs.core.Keyword("\uFDD0:x")).call(null,camera) + cdx),"\uFDD0:y",((new cljs.core.Keyword("\uFDD0:y")).call(null,camera) + cdy)], true);
});
dandy.lcg_next = (function lcg_next(seed){
var next_seed = cljs.core.mod.call(null,((seed * 1103515245) + 12345),4294967296);
var val = ((next_seed >> 16) & 32767);
return cljs.core.PersistentVector.fromArray([next_seed,(val / 32768.0)], true);
});
dandy.flood_unlock = (function flood_unlock(game_map,start_x,start_y){
var target = dandy.kDoor;
var replacement = dandy.kSpace;
if(cljs.core.not_EQ_.call(null,dandy.map_get.call(null,game_map,start_x,start_y),target))
{return game_map;
} else
{var t_map = cljs.core.transient$.call(null,game_map);
var tm = t_map;
var stack = cljs.core.PersistentVector.fromArray([cljs.core.PersistentVector.fromArray([start_x,start_y], true)], true);
while(true){
if(cljs.core.empty_QMARK_.call(null,stack))
{return cljs.core.persistent_BANG_.call(null,tm);
} else
{var vec__3481 = cljs.core.last.call(null,stack);
var cx = cljs.core.nth.call(null,vec__3481,0,null);
var cy = cljs.core.nth.call(null,vec__3481,1,null);
var stack_SINGLEQUOTE_ = cljs.core.pop.call(null,stack);
if(cljs.core._EQ_.call(null,dandy.map_get.call(null,tm,cx,cy),target))
{var tm_SINGLEQUOTE_ = dandy.map_set_transient_BANG_.call(null,tm,cx,cy,replacement);
var new_stack = cljs.core.reduce.call(null,((function (tm,stack,tm_SINGLEQUOTE_,vec__3481,cx,cy,stack_SINGLEQUOTE_){
return (function (s,p__3482){
var vec__3483 = p__3482;
var dx = cljs.core.nth.call(null,vec__3483,0,null);
var dy = cljs.core.nth.call(null,vec__3483,1,null);
var nx = (cx + dx);
var ny = (cy + dy);
if(cljs.core._EQ_.call(null,dandy.map_get.call(null,tm_SINGLEQUOTE_,nx,ny),target))
{return cljs.core.conj.call(null,s,cljs.core.PersistentVector.fromArray([nx,ny], true));
} else
{return s;
}
});})(tm,stack,tm_SINGLEQUOTE_,vec__3481,cx,cy,stack_SINGLEQUOTE_))
,stack_SINGLEQUOTE_,dandy.kNeighborOffsets);
{
var G__3484 = tm_SINGLEQUOTE_;
var G__3485 = new_stack;
tm = G__3484;
stack = G__3485;
continue;
}
} else
{{
var G__3486 = tm;
var G__3487 = stack_SINGLEQUOTE_;
tm = G__3486;
stack = G__3487;
continue;
}
}
}
break;
}
}
});
dandy.do_smart_bomb = (function do_smart_bomb(state,player_idx,active_rect){
var left = (new cljs.core.Keyword("\uFDD0:left")).call(null,active_rect);
var top = (new cljs.core.Keyword("\uFDD0:top")).call(null,active_rect);
var w = (new cljs.core.Keyword("\uFDD0:width")).call(null,active_rect);
var h = (new cljs.core.Keyword("\uFDD0:height")).call(null,active_rect);
var ghost_min = dandy.kMonster1;
var ghost_max = dandy.kMonster3;
var end_x = (left + w);
var end_y = (top + h);
var tm = cljs.core.transient$.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state));
var score = 0;
var y = top;
var x = left;
while(true){
if((y >= end_y))
{return cljs.core.update_in.call(null,cljs.core.assoc.call(null,state,"\uFDD0:map",cljs.core.persistent_BANG_.call(null,tm)),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:score"], true),cljs.core._PLUS_,score);
} else
{if((x >= end_x))
{{
var G__3488 = tm;
var G__3489 = score;
var G__3490 = (y + 1);
var G__3491 = left;
tm = G__3488;
score = G__3489;
y = G__3490;
x = G__3491;
continue;
}
} else
{if("\uFDD0:else")
{var tile = dandy.map_get.call(null,tm,x,y);
if((function (){var and__3941__auto__ = (tile >= ghost_min);
if(and__3941__auto__)
{return (tile <= ghost_max);
} else
{return and__3941__auto__;
}
})())
{{
var G__3492 = dandy.map_set_transient_BANG_.call(null,tm,x,y,0);
var G__3493 = (score + (10 * ((tile - ghost_min) + 1)));
var G__3494 = y;
var G__3495 = (x + 1);
tm = G__3492;
score = G__3493;
y = G__3494;
x = G__3495;
continue;
}
} else
{{
var G__3496 = tm;
var G__3497 = score;
var G__3498 = y;
var G__3499 = (x + 1);
tm = G__3496;
score = G__3497;
y = G__3498;
x = G__3499;
continue;
}
}
} else
{return null;
}
}
}
break;
}
});
dandy.try_move_player = (function try_move_player(state,player_idx,dir){
var player = cljs.core.get_in.call(null,state,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx], true));
var state__$1 = cljs.core.assoc_in.call(null,state,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:dir"], true),dir);
var dx = cljs.core.nth.call(null,dandy.kDirToDeltaX,dir);
var dy = cljs.core.nth.call(null,dandy.kDirToDeltaY,dir);
var nx = ((new cljs.core.Keyword("\uFDD0:x")).call(null,player) + dx);
var ny = ((new cljs.core.Keyword("\uFDD0:y")).call(null,player) + dy);
var v = dandy.map_get.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state__$1),nx,ny);
if(cljs.core._EQ_.call(null,v,dandy.kSpace))
{return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:moved",true,"\uFDD0:state",cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:map"], true),dandy.map_set.call(null,dandy.map_set.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state__$1),(new cljs.core.Keyword("\uFDD0:x")).call(null,player),(new cljs.core.Keyword("\uFDD0:y")).call(null,player),0),nx,ny,(dandy.kPlayer1 + player_idx))),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:x"], true),nx),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:y"], true),ny)], true);
} else
{if(cljs.core._EQ_.call(null,v,dandy.kDoor))
{if(((new cljs.core.Keyword("\uFDD0:keys")).call(null,player) > 0))
{var unlocked_map = dandy.map_set.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state__$1),(new cljs.core.Keyword("\uFDD0:x")).call(null,player),(new cljs.core.Keyword("\uFDD0:y")).call(null,player),0);
var unlocked_map__$1 = dandy.flood_unlock.call(null,unlocked_map,nx,ny);
return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:moved",true,"\uFDD0:state",cljs.core.update_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:map"], true),dandy.map_set.call(null,unlocked_map__$1,nx,ny,(dandy.kPlayer1 + player_idx))),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:x"], true),nx),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:y"], true),ny),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:keys"], true),cljs.core.dec)], true);
} else
{return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:moved",false,"\uFDD0:state",state__$1], true);
}
} else
{if(cljs.core._EQ_.call(null,v,dandy.kDown))
{return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:moved",true,"\uFDD0:state",cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:map"], true),dandy.map_set.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state__$1),(new cljs.core.Keyword("\uFDD0:x")).call(null,player),(new cljs.core.Keyword("\uFDD0:y")).call(null,player),0)),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:escaped"], true),true),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:x"], true),-1),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:y"], true),-1)], true);
} else
{if(cljs.core._EQ_.call(null,v,dandy.kKey))
{return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:moved",true,"\uFDD0:state",cljs.core.update_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:map"], true),dandy.map_set.call(null,dandy.map_set.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state__$1),(new cljs.core.Keyword("\uFDD0:x")).call(null,player),(new cljs.core.Keyword("\uFDD0:y")).call(null,player),0),nx,ny,(dandy.kPlayer1 + player_idx))),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:x"], true),nx),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:y"], true),ny),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:keys"], true),cljs.core.inc)], true);
} else
{if(cljs.core._EQ_.call(null,v,dandy.kFood))
{return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:moved",true,"\uFDD0:state",cljs.core.update_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:map"], true),dandy.map_set.call(null,dandy.map_set.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state__$1),(new cljs.core.Keyword("\uFDD0:x")).call(null,player),(new cljs.core.Keyword("\uFDD0:y")).call(null,player),0),nx,ny,(dandy.kPlayer1 + player_idx))),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:x"], true),nx),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:y"], true),ny),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:health"], true),cljs.core._PLUS_,100)], true);
} else
{if(cljs.core._EQ_.call(null,v,dandy.kMoney))
{return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:moved",true,"\uFDD0:state",cljs.core.update_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:map"], true),dandy.map_set.call(null,dandy.map_set.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state__$1),(new cljs.core.Keyword("\uFDD0:x")).call(null,player),(new cljs.core.Keyword("\uFDD0:y")).call(null,player),0),nx,ny,(dandy.kPlayer1 + player_idx))),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:x"], true),nx),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:y"], true),ny),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:score"], true),cljs.core._PLUS_,100)], true);
} else
{if(cljs.core._EQ_.call(null,v,dandy.kBomb))
{return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:moved",true,"\uFDD0:state",cljs.core.update_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:map"], true),dandy.map_set.call(null,dandy.map_set.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state__$1),(new cljs.core.Keyword("\uFDD0:x")).call(null,player),(new cljs.core.Keyword("\uFDD0:y")).call(null,player),0),nx,ny,(dandy.kPlayer1 + player_idx))),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:x"], true),nx),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:y"], true),ny),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:bombs"], true),cljs.core.inc)], true);
} else
{if("\uFDD0:else")
{return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:moved",false,"\uFDD0:state",state__$1], true);
} else
{return null;
}
}
}
}
}
}
}
}
});
dandy.try_move_player_with_sliding = (function try_move_player_with_sliding(state,player_idx,dir){
var res = dandy.try_move_player.call(null,state,player_idx,dir);
if(cljs.core.truth_((new cljs.core.Keyword("\uFDD0:moved")).call(null,res)))
{return (new cljs.core.Keyword("\uFDD0:state")).call(null,res);
} else
{var dir_l = ((dir + 1) & 7);
var res_l = dandy.try_move_player.call(null,state,player_idx,dir_l);
if(cljs.core.truth_((new cljs.core.Keyword("\uFDD0:moved")).call(null,res_l)))
{return (new cljs.core.Keyword("\uFDD0:state")).call(null,res_l);
} else
{var dir_r = ((dir + 7) & 7);
var res_r = dandy.try_move_player.call(null,state,player_idx,dir_r);
return (new cljs.core.Keyword("\uFDD0:state")).call(null,res_r);
}
}
});
dandy.get_input_direction = (function get_input_direction(input){
var dx = ((cljs.core.not_EQ_.call(null,(input & dandy.kButtonLeft),0))?-1:((cljs.core.not_EQ_.call(null,(input & dandy.kButtonRight),0))?1:(("\uFDD0:else")?0:null)));
var dy = ((cljs.core.not_EQ_.call(null,(input & dandy.kButtonUp),0))?-1:((cljs.core.not_EQ_.call(null,(input & dandy.kButtonDown),0))?1:(("\uFDD0:else")?0:null)));
if((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,dx,0);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,dy,-1);
} else
{return and__3941__auto__;
}
})())
{return 0;
} else
{if((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,dx,1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,dy,-1);
} else
{return and__3941__auto__;
}
})())
{return 1;
} else
{if((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,dx,1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,dy,0);
} else
{return and__3941__auto__;
}
})())
{return 2;
} else
{if((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,dx,1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,dy,1);
} else
{return and__3941__auto__;
}
})())
{return 3;
} else
{if((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,dx,0);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,dy,1);
} else
{return and__3941__auto__;
}
})())
{return 4;
} else
{if((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,dx,-1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,dy,1);
} else
{return and__3941__auto__;
}
})())
{return 5;
} else
{if((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,dx,-1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,dy,0);
} else
{return and__3941__auto__;
}
})())
{return 6;
} else
{if((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,dx,-1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,dy,-1);
} else
{return and__3941__auto__;
}
})())
{return 7;
} else
{if("\uFDD0:else")
{return null;
} else
{return null;
}
}
}
}
}
}
}
}
}
});
dandy.step_player = (function step_player(state,player_idx,active_rect){
var player = cljs.core.get_in.call(null,state,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx], true));
var input = (new cljs.core.Keyword("\uFDD0:input-mask")).call(null,player);
var state__$1 = (((function (){var and__3941__auto__ = cljs.core.not_EQ_.call(null,(input & dandy.kButtonBomb),0);
if(and__3941__auto__)
{return ((new cljs.core.Keyword("\uFDD0:bombs")).call(null,player) > 0);
} else
{return and__3941__auto__;
}
})())?dandy.do_smart_bomb.call(null,cljs.core.update_in.call(null,state,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:bombs"], true),cljs.core.dec),player_idx,active_rect):state);
var player__$1 = cljs.core.get_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx], true));
var dir_opt = dandy.get_input_direction.call(null,input);
if(cljs.core.not_EQ_.call(null,(input & dandy.kButtonFire),0))
{if(((new cljs.core.Keyword("\uFDD0:arrow")).call(null,player__$1) == null))
{var shoot_dir = (function (){var or__3943__auto__ = dir_opt;
if(cljs.core.truth_(or__3943__auto__))
{return or__3943__auto__;
} else
{return (new cljs.core.Keyword("\uFDD0:dir")).call(null,player__$1);
}
})();
return cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:arrow"], true),cljs.core.PersistentArrayMap.fromArray(["\uFDD0:x",(new cljs.core.Keyword("\uFDD0:x")).call(null,player__$1),"\uFDD0:y",(new cljs.core.Keyword("\uFDD0:y")).call(null,player__$1),"\uFDD0:dir",shoot_dir], true));
} else
{return state__$1;
}
} else
{if(cljs.core.truth_(dir_opt))
{return dandy.try_move_player_with_sliding.call(null,state__$1,player_idx,dir_opt);
} else
{return state__$1;
}
}
});
dandy.arrow_tile_val = (function arrow_tile_val(dir){
return (dandy.kArrow + ((dir + 3) & 7));
});
dandy.step_arrow = (function step_arrow(state,player_idx,active_rect){
var player = cljs.core.get_in.call(null,state,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx], true));
var arrow = (new cljs.core.Keyword("\uFDD0:arrow")).call(null,player);
if((arrow == null))
{return state;
} else
{var dx = cljs.core.nth.call(null,dandy.kDirToDeltaX,(new cljs.core.Keyword("\uFDD0:dir")).call(null,arrow));
var dy = cljs.core.nth.call(null,dandy.kDirToDeltaY,(new cljs.core.Keyword("\uFDD0:dir")).call(null,arrow));
var nx = ((new cljs.core.Keyword("\uFDD0:x")).call(null,arrow) + dx);
var ny = ((new cljs.core.Keyword("\uFDD0:y")).call(null,arrow) + dy);
var old_tile = dandy.map_get.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state),(new cljs.core.Keyword("\uFDD0:x")).call(null,arrow),(new cljs.core.Keyword("\uFDD0:y")).call(null,arrow));
var expected_old_val = dandy.arrow_tile_val.call(null,(new cljs.core.Keyword("\uFDD0:dir")).call(null,arrow));
var state__$1 = ((cljs.core._EQ_.call(null,old_tile,expected_old_val))?cljs.core.assoc_in.call(null,state,cljs.core.PersistentVector.fromArray(["\uFDD0:map"], true),dandy.map_set.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state),(new cljs.core.Keyword("\uFDD0:x")).call(null,arrow),(new cljs.core.Keyword("\uFDD0:y")).call(null,arrow),0)):state);
var v = dandy.map_get.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state__$1),nx,ny);
var ghost_min = dandy.kMonster1;
var ghost_max = dandy.kMonster3;
if(cljs.core._EQ_.call(null,v,dandy.kSpace))
{return cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:arrow"], true),cljs.core.PersistentArrayMap.fromArray(["\uFDD0:x",nx,"\uFDD0:y",ny,"\uFDD0:dir",(new cljs.core.Keyword("\uFDD0:dir")).call(null,arrow)], true)),cljs.core.PersistentVector.fromArray(["\uFDD0:map"], true),dandy.map_set.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state__$1),nx,ny,expected_old_val));
} else
{if((function (){var and__3941__auto__ = (v >= ghost_min);
if(and__3941__auto__)
{return (v <= ghost_max);
} else
{return and__3941__auto__;
}
})())
{var new_v = (((v > ghost_min))?(v - 1):0);
var state__$2 = cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:map"], true),dandy.map_set.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state__$1),nx,ny,new_v));
return cljs.core.update_in.call(null,cljs.core.assoc_in.call(null,state__$2,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:arrow"], true),null),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:score"], true),cljs.core._PLUS_,10);
} else
{if(cljs.core._EQ_.call(null,v,dandy.kHeart))
{var dead_active_p = cljs.core.first.call(null,cljs.core.keep.call(null,(function (p){
if(cljs.core.truth_((function (){var and__3941__auto__ = (new cljs.core.Keyword("\uFDD0:active")).call(null,p);
if(cljs.core.truth_(and__3941__auto__))
{return cljs.core.not.call(null,(new cljs.core.Keyword("\uFDD0:alive")).call(null,p));
} else
{return and__3941__auto__;
}
})()))
{return (new cljs.core.Keyword("\uFDD0:id")).call(null,p);
} else
{return null;
}
}),(new cljs.core.Keyword("\uFDD0:players")).call(null,state__$1)));
var new_v = (cljs.core.truth_(dead_active_p)?(dandy.kPlayer1 + dead_active_p):11);
var state__$2 = cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:map"], true),dandy.map_set.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state__$1),nx,ny,new_v));
var state__$3 = (cljs.core.truth_(dead_active_p)?cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,state__$2,cljs.core.PersistentVector.fromArray(["\uFDD0:players",dead_active_p,"\uFDD0:alive"], true),true),cljs.core.PersistentVector.fromArray(["\uFDD0:players",dead_active_p,"\uFDD0:x"], true),nx),cljs.core.PersistentVector.fromArray(["\uFDD0:players",dead_active_p,"\uFDD0:y"], true),ny),cljs.core.PersistentVector.fromArray(["\uFDD0:players",dead_active_p,"\uFDD0:health"], true),50):state__$2);
return cljs.core.assoc_in.call(null,state__$3,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:arrow"], true),null);
} else
{if(cljs.core._EQ_.call(null,v,dandy.kBomb))
{return dandy.do_smart_bomb.call(null,cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:arrow"], true),null),player_idx,active_rect);
} else
{if("\uFDD0:else")
{return cljs.core.assoc_in.call(null,state__$1,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:arrow"], true),null);
} else
{return null;
}
}
}
}
}
}
});
dandy.is_generator_blocked_QMARK_ = (function is_generator_blocked_QMARK_(game_map,gx,gy){
var dirs = cljs.core.PersistentVector.fromArray([0,2,4,6], true);
var unblocked_QMARK_ = cljs.core.some.call(null,((function (dirs){
return (function (dir){
var dx = cljs.core.nth.call(null,dandy.kDirToDeltaX,dir);
var dy = cljs.core.nth.call(null,dandy.kDirToDeltaY,dir);
var nx = (gx + dx);
var ny = (gy + dy);
return cljs.core._EQ_.call(null,dandy.map_get.call(null,game_map,nx,ny),0);
});})(dirs))
,dirs);
return cljs.core.not.call(null,unblocked_QMARK_);
});
dandy.is_ghost_blocked_QMARK_ = (function is_ghost_blocked_QMARK_(state,gx,gy){
var players = (new cljs.core.Keyword("\uFDD0:players")).call(null,state);
var active_alive_p = cljs.core.filter.call(null,((function (players){
return (function (p){
var and__3941__auto__ = (new cljs.core.Keyword("\uFDD0:active")).call(null,p);
if(cljs.core.truth_(and__3941__auto__))
{var and__3941__auto____$1 = (new cljs.core.Keyword("\uFDD0:alive")).call(null,p);
if(cljs.core.truth_(and__3941__auto____$1))
{return cljs.core.not.call(null,(new cljs.core.Keyword("\uFDD0:escaped")).call(null,p));
} else
{return and__3941__auto____$1;
}
} else
{return and__3941__auto__;
}
});})(players))
,players);
if(cljs.core.empty_QMARK_.call(null,active_alive_p))
{return true;
} else
{var best_p = cljs.core.first.call(null,cljs.core.sort_by.call(null,(function (p){
return (dandy.abs.call(null,((new cljs.core.Keyword("\uFDD0:x")).call(null,p) - gx)) + dandy.abs.call(null,((new cljs.core.Keyword("\uFDD0:y")).call(null,p) - gy)));
}),active_alive_p));
var px = (new cljs.core.Keyword("\uFDD0:x")).call(null,best_p);
var py = (new cljs.core.Keyword("\uFDD0:y")).call(null,best_p);
var dx = (px - gx);
var dy = (py - gy);
var sgn = ((function (best_p,px,py,dx,dy){
return (function (v){
if((v > 0))
{return 1;
} else
{if((v < 0))
{return -1;
} else
{if("\uFDD0:else")
{return 0;
} else
{return null;
}
}
}
});})(best_p,px,py,dx,dy))
;
var sdx = sgn.call(null,dx);
var sdy = sgn.call(null,dy);
var m_dir = (((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,0);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,-1);
} else
{return and__3941__auto__;
}
})())?0:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,-1);
} else
{return and__3941__auto__;
}
})())?1:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,0);
} else
{return and__3941__auto__;
}
})())?2:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,1);
} else
{return and__3941__auto__;
}
})())?3:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,0);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,1);
} else
{return and__3941__auto__;
}
})())?4:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,-1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,1);
} else
{return and__3941__auto__;
}
})())?5:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,-1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,0);
} else
{return and__3941__auto__;
}
})())?6:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,-1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,-1);
} else
{return and__3941__auto__;
}
})())?7:(("\uFDD0:else")?0:null)))))))));
var search_offsets = cljs.core.PersistentVector.fromArray([0,7,1], true);
var unblocked_QMARK_ = cljs.core.some.call(null,((function (best_p,px,py,dx,dy,sgn,sdx,sdy,m_dir,search_offsets){
return (function (offset){
var d = ((m_dir + offset) & 7);
var nx = (gx + cljs.core.nth.call(null,dandy.kDirToDeltaX,d));
var ny = (gy + cljs.core.nth.call(null,dandy.kDirToDeltaY,d));
var nv = dandy.map_get.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state),nx,ny);
var or__3943__auto__ = cljs.core._EQ_.call(null,nv,0);
if(or__3943__auto__)
{return or__3943__auto__;
} else
{var and__3941__auto__ = (nv >= dandy.kPlayer1);
if(and__3941__auto__)
{return (nv <= (dandy.kPlayer1 + 3));
} else
{return and__3941__auto__;
}
}
});})(best_p,px,py,dx,dy,sgn,sdx,sdy,m_dir,search_offsets))
,search_offsets);
return cljs.core.not.call(null,unblocked_QMARK_);
}
});
dandy.hurt_player = (function hurt_player(state,t_map,player_idx,pain){
var player = cljs.core.get_in.call(null,state,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx], true));
if(((new cljs.core.Keyword("\uFDD0:health")).call(null,player) > pain))
{return cljs.core.PersistentVector.fromArray([cljs.core.update_in.call(null,state,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:health"], true),cljs.core._,pain),t_map], true);
} else
{var remains = ((((new cljs.core.Keyword("\uFDD0:keys")).call(null,player) > 0))?dandy.kKey:dandy.kSpace);
var t_map_SINGLEQUOTE_ = dandy.map_set_transient_BANG_.call(null,t_map,(new cljs.core.Keyword("\uFDD0:x")).call(null,player),(new cljs.core.Keyword("\uFDD0:y")).call(null,player),remains);
var state_SINGLEQUOTE_ = cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,state,cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:health"], true),0),cljs.core.PersistentVector.fromArray(["\uFDD0:players",player_idx,"\uFDD0:alive"], true),false);
return cljs.core.PersistentVector.fromArray([state_SINGLEQUOTE_,t_map_SINGLEQUOTE_], true);
}
});
dandy.step_ghost = (function step_ghost(state,t_map,gx,gy,ghost_val){
var players = (new cljs.core.Keyword("\uFDD0:players")).call(null,state);
var active_alive_p = cljs.core.filter.call(null,((function (players){
return (function (p){
var and__3941__auto__ = (new cljs.core.Keyword("\uFDD0:active")).call(null,p);
if(cljs.core.truth_(and__3941__auto__))
{var and__3941__auto____$1 = (new cljs.core.Keyword("\uFDD0:alive")).call(null,p);
if(cljs.core.truth_(and__3941__auto____$1))
{return cljs.core.not.call(null,(new cljs.core.Keyword("\uFDD0:escaped")).call(null,p));
} else
{return and__3941__auto____$1;
}
} else
{return and__3941__auto__;
}
});})(players))
,players);
if(cljs.core.empty_QMARK_.call(null,active_alive_p))
{return cljs.core.PersistentVector.fromArray([state,t_map], true);
} else
{var best_p = cljs.core.first.call(null,cljs.core.sort_by.call(null,(function (p){
return (dandy.abs.call(null,((new cljs.core.Keyword("\uFDD0:x")).call(null,p) - gx)) + dandy.abs.call(null,((new cljs.core.Keyword("\uFDD0:y")).call(null,p) - gy)));
}),active_alive_p));
var px = (new cljs.core.Keyword("\uFDD0:x")).call(null,best_p);
var py = (new cljs.core.Keyword("\uFDD0:y")).call(null,best_p);
var dx = (px - gx);
var dy = (py - gy);
var sgn = ((function (best_p,px,py,dx,dy){
return (function (v){
if((v > 0))
{return 1;
} else
{if((v < 0))
{return -1;
} else
{if("\uFDD0:else")
{return 0;
} else
{return null;
}
}
}
});})(best_p,px,py,dx,dy))
;
var sdx = sgn.call(null,dx);
var sdy = sgn.call(null,dy);
var m_dir = (((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,0);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,-1);
} else
{return and__3941__auto__;
}
})())?0:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,-1);
} else
{return and__3941__auto__;
}
})())?1:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,0);
} else
{return and__3941__auto__;
}
})())?2:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,1);
} else
{return and__3941__auto__;
}
})())?3:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,0);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,1);
} else
{return and__3941__auto__;
}
})())?4:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,-1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,1);
} else
{return and__3941__auto__;
}
})())?5:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,-1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,0);
} else
{return and__3941__auto__;
}
})())?6:(((function (){var and__3941__auto__ = cljs.core._EQ_.call(null,sdx,-1);
if(and__3941__auto__)
{return cljs.core._EQ_.call(null,sdy,-1);
} else
{return and__3941__auto__;
}
})())?7:(("\uFDD0:else")?0:null)))))))));
var search_offsets = cljs.core.PersistentVector.fromArray([0,7,1], true);
var offsets = search_offsets;
while(true){
if(cljs.core.empty_QMARK_.call(null,offsets))
{return cljs.core.PersistentVector.fromArray([state,t_map], true);
} else
{var offset = cljs.core.first.call(null,offsets);
var d = ((m_dir + offset) & 7);
var nx = (gx + cljs.core.nth.call(null,dandy.kDirToDeltaX,d));
var ny = (gy + cljs.core.nth.call(null,dandy.kDirToDeltaY,d));
var nv = dandy.map_get.call(null,t_map,nx,ny);
if(cljs.core._EQ_.call(null,nv,dandy.kSpace))
{return cljs.core.PersistentVector.fromArray([state,dandy.map_set_transient_BANG_.call(null,dandy.map_set_transient_BANG_.call(null,t_map,gx,gy,0),nx,ny,ghost_val)], true);
} else
{if((function (){var and__3941__auto__ = (nv >= dandy.kPlayer1);
if(and__3941__auto__)
{return (nv <= (dandy.kPlayer1 + 3));
} else
{return and__3941__auto__;
}
})())
{var hit_player_idx = (nv - dandy.kPlayer1);
var pain = (10 * ((ghost_val - dandy.kMonster1) + 1));
var vec__3501 = dandy.hurt_player.call(null,state,t_map,hit_player_idx,pain);
var state_SINGLEQUOTE_ = cljs.core.nth.call(null,vec__3501,0,null);
var t_map_SINGLEQUOTE_ = cljs.core.nth.call(null,vec__3501,1,null);
var t_map_SINGLEQUOTE__SINGLEQUOTE_ = dandy.map_set_transient_BANG_.call(null,t_map_SINGLEQUOTE_,gx,gy,0);
return cljs.core.PersistentVector.fromArray([state_SINGLEQUOTE_,t_map_SINGLEQUOTE__SINGLEQUOTE_], true);
} else
{if((function (){var and__3941__auto__ = (nv >= dandy.kArrow);
if(and__3941__auto__)
{return (nv <= (dandy.kArrow + 7));
} else
{return and__3941__auto__;
}
})())
{return cljs.core.PersistentVector.fromArray([state,t_map], true);
} else
{if("\uFDD0:else")
{{
var G__3502 = cljs.core.rest.call(null,offsets);
offsets = G__3502;
continue;
}
} else
{return null;
}
}
}
}
}
break;
}
}
});
dandy.step_generator = (function step_generator(state,t_map,gx,gy,gen_val){
var vec__3505 = dandy.lcg_next.call(null,(new cljs.core.Keyword("\uFDD0:rng-state")).call(null,state));
var rng_state = cljs.core.nth.call(null,vec__3505,0,null);
var ran = cljs.core.nth.call(null,vec__3505,1,null);
var state__$1 = cljs.core.assoc.call(null,state,"\uFDD0:rng-state",rng_state);
if((ran < 0.3))
{var vec__3506 = dandy.lcg_next.call(null,(new cljs.core.Keyword("\uFDD0:rng-state")).call(null,state__$1));
var rng_state2 = cljs.core.nth.call(null,vec__3506,0,null);
var ran_dir = cljs.core.nth.call(null,vec__3506,1,null);
var state__$2 = cljs.core.assoc.call(null,state__$1,"\uFDD0:rng-state",rng_state2);
var dir_idx = (Math.floor((ran_dir * 4.0)) | 0);
var dir = (dir_idx * 2);
var dx = cljs.core.nth.call(null,dandy.kDirToDeltaX,dir);
var dy = cljs.core.nth.call(null,dandy.kDirToDeltaY,dir);
var nx = (gx + dx);
var ny = (gy + dy);
if(cljs.core._EQ_.call(null,dandy.map_get.call(null,t_map,nx,ny),0))
{var new_ghost = (dandy.kMonster1 + (gen_val - dandy.kGenerator1));
var t_map_SINGLEQUOTE_ = dandy.map_set_transient_BANG_.call(null,t_map,nx,ny,new_ghost);
return cljs.core.PersistentVector.fromArray([state__$2,t_map_SINGLEQUOTE_], true);
} else
{return cljs.core.PersistentVector.fromArray([state__$2,t_map], true);
}
} else
{return cljs.core.PersistentVector.fromArray([state__$1,t_map], true);
}
});
dandy.step_enemies = (function step_enemies(state,active_rect){
var rotor = (((new cljs.core.Keyword("\uFDD0:rotor")).call(null,state) + 1) & 3);
var rx = (rotor & 1);
var ry = ((rotor >> 1) & 1);
var x_start = (dandy.align_even.call(null,((new cljs.core.Keyword("\uFDD0:left")).call(null,active_rect) + 1)) + rx);
var y_start = (dandy.align_even.call(null,((new cljs.core.Keyword("\uFDD0:top")).call(null,active_rect) + 1)) + ry);
var x_end = ((new cljs.core.Keyword("\uFDD0:left")).call(null,active_rect) + (new cljs.core.Keyword("\uFDD0:width")).call(null,active_rect));
var y_end = ((new cljs.core.Keyword("\uFDD0:top")).call(null,active_rect) + (new cljs.core.Keyword("\uFDD0:height")).call(null,active_rect));
var state_SINGLEQUOTE_ = cljs.core.assoc.call(null,state,"\uFDD0:rotor",rotor);
var t_map = cljs.core.transient$.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state_SINGLEQUOTE_));
var vec__3510 = (function (){var s = state_SINGLEQUOTE_;
var tm = t_map;
var y = y_start;
var x = x_start;
while(true){
if((y >= y_end))
{return cljs.core.PersistentVector.fromArray([s,tm], true);
} else
{if((x >= x_end))
{{
var G__3513 = s;
var G__3514 = tm;
var G__3515 = (y + 2);
var G__3516 = x_start;
s = G__3513;
tm = G__3514;
y = G__3515;
x = G__3516;
continue;
}
} else
{if("\uFDD0:else")
{var v = dandy.map_get.call(null,tm,x,y);
if((function (){var and__3941__auto__ = (v >= dandy.kMonster1);
if(and__3941__auto__)
{return (v <= dandy.kMonster3);
} else
{return and__3941__auto__;
}
})())
{var vec__3511 = dandy.step_ghost.call(null,s,tm,x,y,v);
var s_SINGLEQUOTE_ = cljs.core.nth.call(null,vec__3511,0,null);
var tm_SINGLEQUOTE_ = cljs.core.nth.call(null,vec__3511,1,null);
{
var G__3517 = s_SINGLEQUOTE_;
var G__3518 = tm_SINGLEQUOTE_;
var G__3519 = y;
var G__3520 = (x + 2);
s = G__3517;
tm = G__3518;
y = G__3519;
x = G__3520;
continue;
}
} else
{if((function (){var and__3941__auto__ = (v >= dandy.kGenerator1);
if(and__3941__auto__)
{return (v <= dandy.kGenerator3);
} else
{return and__3941__auto__;
}
})())
{var vec__3512 = dandy.step_generator.call(null,s,tm,x,y,v);
var s_SINGLEQUOTE_ = cljs.core.nth.call(null,vec__3512,0,null);
var tm_SINGLEQUOTE_ = cljs.core.nth.call(null,vec__3512,1,null);
{
var G__3521 = s_SINGLEQUOTE_;
var G__3522 = tm_SINGLEQUOTE_;
var G__3523 = y;
var G__3524 = (x + 2);
s = G__3521;
tm = G__3522;
y = G__3523;
x = G__3524;
continue;
}
} else
{if("\uFDD0:else")
{{
var G__3525 = s;
var G__3526 = tm;
var G__3527 = y;
var G__3528 = (x + 2);
s = G__3525;
tm = G__3526;
y = G__3527;
x = G__3528;
continue;
}
} else
{return null;
}
}
}
} else
{return null;
}
}
}
break;
}
})();
var final_state = cljs.core.nth.call(null,vec__3510,0,null);
var final_t_map = cljs.core.nth.call(null,vec__3510,1,null);
return cljs.core.assoc.call(null,final_state,"\uFDD0:map",cljs.core.persistent_BANG_.call(null,final_t_map));
});
dandy.load_level_into_state = (function load_level_into_state(state,level_idx){
var raw_map = dandy.load_level_map.call(null,level_idx);
var spawn_pos = dandy.map_find.call(null,raw_map,3);
var spawn = (cljs.core.truth_(spawn_pos)?spawn_pos:cljs.core.PersistentVector.fromArray([2,2], true));
var players = cljs.core.vec.call(null,cljs.core.map.call(null,((function (raw_map,spawn_pos,spawn){
return (function (p){
if(cljs.core.truth_((new cljs.core.Keyword("\uFDD0:active")).call(null,p)))
{var idx = (new cljs.core.Keyword("\uFDD0:id")).call(null,p);
var dir = cljs.core.nth.call(null,dandy.PLAYER_SPAWN_DIRS,idx);
var px = (cljs.core.first.call(null,spawn) + cljs.core.nth.call(null,dandy.kDirToDeltaX,dir));
var py = (cljs.core.second.call(null,spawn) + cljs.core.nth.call(null,dandy.kDirToDeltaY,dir));
return cljs.core.assoc.call(null,p,"\uFDD0:alive",true,"\uFDD0:escaped",false,"\uFDD0:x",px,"\uFDD0:y",py,"\uFDD0:dir",dir,"\uFDD0:health",100,"\uFDD0:bombs",0,"\uFDD0:keys",0,"\uFDD0:arrow",null);
} else
{return p;
}
});})(raw_map,spawn_pos,spawn))
,(new cljs.core.Keyword("\uFDD0:players")).call(null,state)));
var game_map = cljs.core.reduce.call(null,((function (raw_map,spawn_pos,spawn,players){
return (function (m,p){
if(cljs.core.truth_((new cljs.core.Keyword("\uFDD0:active")).call(null,p)))
{return dandy.map_set.call(null,m,(new cljs.core.Keyword("\uFDD0:x")).call(null,p),(new cljs.core.Keyword("\uFDD0:y")).call(null,p),(dandy.kPlayer1 + (new cljs.core.Keyword("\uFDD0:id")).call(null,p)));
} else
{return m;
}
});})(raw_map,spawn_pos,spawn,players))
,raw_map,players);
return cljs.core.assoc.call(null,cljs.core.assoc.call(null,cljs.core.assoc.call(null,cljs.core.assoc.call(null,cljs.core.assoc.call(null,state,"\uFDD0:map",game_map),"\uFDD0:level-idx",level_idx),"\uFDD0:players",players),"\uFDD0:rotor",0),"\uFDD0:camera",(function (){var vec__3530 = dandy.calculate_target_cog.call(null,players);
var tx = cljs.core.nth.call(null,vec__3530,0,null);
var ty = cljs.core.nth.call(null,vec__3530,1,null);
return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:x",tx,"\uFDD0:y",ty], true);
})());
});
dandy.check_level_progression = (function check_level_progression(state){
var players = (new cljs.core.Keyword("\uFDD0:players")).call(null,state);
var any_joined = cljs.core.some.call(null,"\uFDD0:active",players);
var players_in_dungeon = cljs.core.some.call(null,((function (players,any_joined){
return (function (p){
var and__3941__auto__ = (new cljs.core.Keyword("\uFDD0:active")).call(null,p);
if(cljs.core.truth_(and__3941__auto__))
{var and__3941__auto____$1 = (new cljs.core.Keyword("\uFDD0:alive")).call(null,p);
if(cljs.core.truth_(and__3941__auto____$1))
{return cljs.core.not.call(null,(new cljs.core.Keyword("\uFDD0:escaped")).call(null,p));
} else
{return and__3941__auto____$1;
}
} else
{return and__3941__auto__;
}
});})(players,any_joined))
,players);
var any_escaped = cljs.core.some.call(null,((function (players,any_joined,players_in_dungeon){
return (function (p){
var and__3941__auto__ = (new cljs.core.Keyword("\uFDD0:active")).call(null,p);
if(cljs.core.truth_(and__3941__auto__))
{return (new cljs.core.Keyword("\uFDD0:escaped")).call(null,p);
} else
{return and__3941__auto__;
}
});})(players,any_joined,players_in_dungeon))
,players);
var arrows_in_flight = cljs.core.some.call(null,((function (players,any_joined,players_in_dungeon,any_escaped){
return (function (p){
var and__3941__auto__ = (new cljs.core.Keyword("\uFDD0:active")).call(null,p);
if(cljs.core.truth_(and__3941__auto__))
{return !(((new cljs.core.Keyword("\uFDD0:arrow")).call(null,p) == null));
} else
{return and__3941__auto__;
}
});})(players,any_joined,players_in_dungeon,any_escaped))
,players);
if(cljs.core.truth_((function (){var and__3941__auto__ = any_joined;
if(cljs.core.truth_(and__3941__auto__))
{var and__3941__auto____$1 = cljs.core.not.call(null,players_in_dungeon);
if(and__3941__auto____$1)
{return cljs.core.not.call(null,arrows_in_flight);
} else
{return and__3941__auto____$1;
}
} else
{return and__3941__auto__;
}
})()))
{if(cljs.core.truth_(any_escaped))
{var next_level = ((((new cljs.core.Keyword("\uFDD0:level-idx")).call(null,state) + 1) < 25) ? ((new cljs.core.Keyword("\uFDD0:level-idx")).call(null,state) + 1) : 25);
return dandy.load_level_into_state.call(null,state,next_level);
} else
{return dandy.load_level_into_state.call(null,state,(new cljs.core.Keyword("\uFDD0:level-idx")).call(null,state));
}
} else
{return state;
}
});
dandy.check_hot_joins = (function check_hot_joins(state){
return cljs.core.reduce.call(null,(function (s,idx){
var p = cljs.core.get_in.call(null,s,cljs.core.PersistentVector.fromArray(["\uFDD0:players",idx], true));
if((function (){var and__3941__auto__ = cljs.core.not.call(null,(new cljs.core.Keyword("\uFDD0:active")).call(null,p));
if(and__3941__auto__)
{return cljs.core.not_EQ_.call(null,(new cljs.core.Keyword("\uFDD0:input-mask")).call(null,p),0);
} else
{return and__3941__auto__;
}
})())
{var spawn_pos = dandy.map_find.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,s),3);
var spawn = (cljs.core.truth_(spawn_pos)?spawn_pos:cljs.core.PersistentVector.fromArray([2,2], true));
var dir = cljs.core.nth.call(null,dandy.PLAYER_SPAWN_DIRS,idx);
var dx = cljs.core.nth.call(null,dandy.kDirToDeltaX,dir);
var dy = cljs.core.nth.call(null,dandy.kDirToDeltaY,dir);
var px = (cljs.core.first.call(null,spawn) + dx);
var py = (cljs.core.second.call(null,spawn) + dy);
var p_SINGLEQUOTE_ = cljs.core.assoc.call(null,p,"\uFDD0:active",true,"\uFDD0:alive",true,"\uFDD0:escaped",false,"\uFDD0:x",px,"\uFDD0:y",py,"\uFDD0:dir",dir,"\uFDD0:health",100,"\uFDD0:score",0,"\uFDD0:bombs",0,"\uFDD0:keys",0,"\uFDD0:arrow",null);
var state_SINGLEQUOTE_ = cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,s,cljs.core.PersistentVector.fromArray(["\uFDD0:players",idx], true),p_SINGLEQUOTE_),cljs.core.PersistentVector.fromArray(["\uFDD0:map"], true),dandy.map_set.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,s),px,py,(dandy.kPlayer1 + idx)));
return state_SINGLEQUOTE_;
} else
{return s;
}
}),state,cljs.core.range.call(null,4));
});
dandy.can_sleep_QMARK_ = (function can_sleep_QMARK_(state){
var players = (new cljs.core.Keyword("\uFDD0:players")).call(null,state);
var has_inputs = cljs.core.some.call(null,((function (players){
return (function (p){
var and__3941__auto__ = (new cljs.core.Keyword("\uFDD0:active")).call(null,p);
if(cljs.core.truth_(and__3941__auto__))
{return cljs.core.not_EQ_.call(null,(new cljs.core.Keyword("\uFDD0:input-mask")).call(null,p),0);
} else
{return and__3941__auto__;
}
});})(players))
,players);
var has_arrows = cljs.core.some.call(null,((function (players,has_inputs){
return (function (p){
var and__3941__auto__ = (new cljs.core.Keyword("\uFDD0:active")).call(null,p);
if(cljs.core.truth_(and__3941__auto__))
{return !(((new cljs.core.Keyword("\uFDD0:arrow")).call(null,p) == null));
} else
{return and__3941__auto__;
}
});})(players,has_inputs))
,players);
var camera = (new cljs.core.Keyword("\uFDD0:camera")).call(null,state);
var vec__3532 = dandy.calculate_target_cog.call(null,players);
var tx = cljs.core.nth.call(null,vec__3532,0,null);
var ty = cljs.core.nth.call(null,vec__3532,1,null);
var dx = (tx - (new cljs.core.Keyword("\uFDD0:x")).call(null,camera));
var dy = (ty - (new cljs.core.Keyword("\uFDD0:y")).call(null,camera));
var camera_arrived = (function (){var and__3941__auto__ = (dandy.abs.call(null,dx) < 0.1);
if(and__3941__auto__)
{return (dandy.abs.call(null,dy) < 0.1);
} else
{return and__3941__auto__;
}
})();
if(cljs.core.truth_((function (){var or__3943__auto__ = has_inputs;
if(cljs.core.truth_(or__3943__auto__))
{return or__3943__auto__;
} else
{var or__3943__auto____$1 = has_arrows;
if(cljs.core.truth_(or__3943__auto____$1))
{return or__3943__auto____$1;
} else
{return cljs.core.not.call(null,camera_arrived);
}
}
})()))
{return false;
} else
{var active_rect = dandy.get_active_rect.call(null,camera);
var left = (new cljs.core.Keyword("\uFDD0:left")).call(null,active_rect);
var top = (new cljs.core.Keyword("\uFDD0:top")).call(null,active_rect);
var w = (new cljs.core.Keyword("\uFDD0:width")).call(null,active_rect);
var h = (new cljs.core.Keyword("\uFDD0:height")).call(null,active_rect);
var end_x = (left + w);
var end_y = (top + h);
var any_active_QMARK_ = (function (){var y = top;
var x = left;
while(true){
if((y >= end_y))
{return false;
} else
{if((x >= end_x))
{{
var G__3533 = (y + 1);
var G__3534 = left;
y = G__3533;
x = G__3534;
continue;
}
} else
{if("\uFDD0:else")
{var v = dandy.map_get.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state),x,y);
if(cljs.core.truth_((((function (){var and__3941__auto__ = (v >= dandy.kMonster1);
if(and__3941__auto__)
{return (v <= dandy.kMonster3);
} else
{return and__3941__auto__;
}
})())?cljs.core.not.call(null,dandy.is_ghost_blocked_QMARK_.call(null,state,x,y)):(((function (){var and__3941__auto__ = (v >= dandy.kGenerator1);
if(and__3941__auto__)
{return (v <= dandy.kGenerator3);
} else
{return and__3941__auto__;
}
})())?cljs.core.not.call(null,dandy.is_generator_blocked_QMARK_.call(null,(new cljs.core.Keyword("\uFDD0:map")).call(null,state),x,y)):(("\uFDD0:else")?false:null)))))
{return true;
} else
{{
var G__3535 = y;
var G__3536 = (x + 1);
y = G__3535;
x = G__3536;
continue;
}
}
} else
{return null;
}
}
}
break;
}
})();
return cljs.core.not.call(null,any_active_QMARK_);
}
});
dandy.step_game = (function step_game(state){
var state__$1 = cljs.core.update_in.call(null,state,cljs.core.PersistentVector.fromArray(["\uFDD0:time"], true),cljs.core.inc);
var state__$2 = dandy.check_hot_joins.call(null,state__$1);
var should_move = cljs.core._EQ_.call(null,cljs.core.mod.call(null,(new cljs.core.Keyword("\uFDD0:time")).call(null,state__$2),4),0);
if(should_move)
{var active_rect = dandy.get_active_rect.call(null,(new cljs.core.Keyword("\uFDD0:camera")).call(null,state__$2));
var state__$3 = cljs.core.reduce.call(null,((function (active_rect){
return (function (s,idx){
var p = cljs.core.get_in.call(null,s,cljs.core.PersistentVector.fromArray(["\uFDD0:players",idx], true));
if(cljs.core.truth_((function (){var and__3941__auto__ = (new cljs.core.Keyword("\uFDD0:active")).call(null,p);
if(cljs.core.truth_(and__3941__auto__))
{var and__3941__auto____$1 = (new cljs.core.Keyword("\uFDD0:alive")).call(null,p);
if(cljs.core.truth_(and__3941__auto____$1))
{return cljs.core.not.call(null,(new cljs.core.Keyword("\uFDD0:escaped")).call(null,p));
} else
{return and__3941__auto____$1;
}
} else
{return and__3941__auto__;
}
})()))
{return dandy.step_player.call(null,s,idx,active_rect);
} else
{return s;
}
});})(active_rect))
,state__$2,cljs.core.range.call(null,4));
var state__$4 = cljs.core.reduce.call(null,((function (active_rect,state__$3){
return (function (s,idx){
var p = cljs.core.get_in.call(null,s,cljs.core.PersistentVector.fromArray(["\uFDD0:players",idx], true));
if(cljs.core.truth_((new cljs.core.Keyword("\uFDD0:active")).call(null,p)))
{return dandy.step_arrow.call(null,s,idx,active_rect);
} else
{return s;
}
});})(active_rect,state__$3))
,state__$3,cljs.core.range.call(null,4));
var state__$5 = dandy.step_enemies.call(null,state__$4,active_rect);
var state__$6 = dandy.check_level_progression.call(null,state__$5);
return cljs.core.assoc.call(null,state__$6,"\uFDD0:camera",dandy.update_camera.call(null,(new cljs.core.Keyword("\uFDD0:camera")).call(null,state__$6),(new cljs.core.Keyword("\uFDD0:players")).call(null,state__$6)));
} else
{return cljs.core.assoc.call(null,state__$2,"\uFDD0:camera",dandy.update_camera.call(null,(new cljs.core.Keyword("\uFDD0:camera")).call(null,state__$2),(new cljs.core.Keyword("\uFDD0:players")).call(null,state__$2)));
}
});
dandy.init_player = (function init_player(id,active){
return cljs.core.PersistentHashMap.fromArrays(["\uFDD0:bombs","\uFDD0:health","\uFDD0:y","\uFDD0:score","\uFDD0:x","\uFDD0:dir","\uFDD0:arrow","\uFDD0:input-mask","\uFDD0:escaped","\uFDD0:active","\uFDD0:alive","\uFDD0:keys","\uFDD0:id"],[0,100,-1,0,-1,cljs.core.nth.call(null,dandy.PLAYER_SPAWN_DIRS,id),null,0,false,active,active,0,id]);
});
dandy.init_game_state = (function init_game_state(level_idx){
var raw_map = dandy.load_level_map.call(null,level_idx);
var spawn_pos = dandy.map_find.call(null,raw_map,3);
var spawn = (cljs.core.truth_(spawn_pos)?spawn_pos:cljs.core.PersistentVector.fromArray([2,2], true));
var players = cljs.core.vec.call(null,cljs.core.map.call(null,((function (raw_map,spawn_pos,spawn){
return (function (id){
return dandy.init_player.call(null,id,cljs.core._EQ_.call(null,id,0));
});})(raw_map,spawn_pos,spawn))
,cljs.core.range.call(null,4)));
var p1_dir = cljs.core.nth.call(null,dandy.PLAYER_SPAWN_DIRS,0);
var p1_x = (cljs.core.first.call(null,spawn) + cljs.core.nth.call(null,dandy.kDirToDeltaX,p1_dir));
var p1_y = (cljs.core.second.call(null,spawn) + cljs.core.nth.call(null,dandy.kDirToDeltaY,p1_dir));
var players__$1 = cljs.core.assoc_in.call(null,players,cljs.core.PersistentVector.fromArray([0,"\uFDD0:x"], true),p1_x);
var players__$2 = cljs.core.assoc_in.call(null,players__$1,cljs.core.PersistentVector.fromArray([0,"\uFDD0:y"], true),p1_y);
var game_map = dandy.map_set.call(null,raw_map,p1_x,p1_y,(dandy.kPlayer1 + 0));
return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:map",game_map,"\uFDD0:level-idx",level_idx,"\uFDD0:players",players__$2,"\uFDD0:camera",cljs.core.PersistentArrayMap.fromArray(["\uFDD0:x",(cljs.core.first.call(null,spawn) * 16),"\uFDD0:y",(cljs.core.second.call(null,spawn) * 16)], true),"\uFDD0:rotor",0,"\uFDD0:time",0,"\uFDD0:rng-state",12345], true);
});
dandy.runtime_state = cljs.core.atom.call(null,cljs.core.PersistentArrayMap.fromArray(["\uFDD0:game-state",dandy.init_game_state.call(null,0),"\uFDD0:pressed-keys",cljs.core.PersistentHashSet.EMPTY,"\uFDD0:anim-frame-id",null,"\uFDD0:is-sleeping",false,"\uFDD0:gamepad-poll-interval",null,"\uFDD0:last-hud-state",cljs.core.ObjMap.EMPTY,"\uFDD0:dom-elements",null], true));
dandy.draw_game = (function draw_game(canvas,strike,game_state){
var tile_w = 16;
var tile_h = 16;
var scale = dandy.tileScale;
var canvas_tile_w = (scale * tile_w);
var canvas_tile_h = (scale * tile_h);
var context = canvas.getContext("2d");
var cw = canvas.width;
var ch = canvas.height;
var offsets = dandy.get_camera_offsets.call(null,(new cljs.core.Keyword("\uFDD0:camera")).call(null,game_state));
var offset_x = (offsets[0]);
var offset_y = (offsets[1]);
var canvas_offset_x = (offset_x * scale);
var canvas_offset_y = (offset_y * scale);
var active_rect = dandy.get_active_rect.call(null,(new cljs.core.Keyword("\uFDD0:camera")).call(null,game_state));
var left = (new cljs.core.Keyword("\uFDD0:left")).call(null,active_rect);
var top = (new cljs.core.Keyword("\uFDD0:top")).call(null,active_rect);
var w = (new cljs.core.Keyword("\uFDD0:width")).call(null,active_rect);
var h = (new cljs.core.Keyword("\uFDD0:height")).call(null,active_rect);
var end_x = (left + w);
var end_y = (top + h);
var game_map = (new cljs.core.Keyword("\uFDD0:map")).call(null,game_state);
context.imageSmoothingEnabled = false;
context.clearRect(0,0,cw,ch);
var cols = (end_x - left);
var rows = (end_y - top);
var n__3122__auto__ = rows;
var r = 0;
while(true){
if((r < n__3122__auto__))
{var y_3537 = (top + r);
var n__3122__auto___3538__$1 = cols;
var c_3539 = 0;
while(true){
if((c_3539 < n__3122__auto___3538__$1))
{var x_3540 = (left + c_3539);
var d_3541 = dandy.map_get.call(null,game_map,x_3540,y_3537);
var tx_3542 = (tile_w * (d_3541 & 15));
var ty_3543 = (tile_h * (d_3541 >> 4));
context.drawImage(strike,tx_3542,ty_3543,tile_w,tile_h,(canvas_offset_x + (x_3540 * canvas_tile_w)),(canvas_offset_y + (y_3537 * canvas_tile_h)),canvas_tile_w,canvas_tile_h);
{
var G__3544 = (c_3539 + 1);
c_3539 = G__3544;
continue;
}
} else
{}
break;
}
{
var G__3545 = (r + 1);
r = G__3545;
continue;
}
} else
{return null;
}
break;
}
});
dandy.update_hud = (function update_hud(state){
var dom_players = cljs.core.get_in.call(null,cljs.core.deref.call(null,dandy.runtime_state),cljs.core.PersistentVector.fromArray(["\uFDD0:dom-elements","\uFDD0:players"], true));
var last_hud = (new cljs.core.Keyword("\uFDD0:last-hud-state")).call(null,cljs.core.deref.call(null,dandy.runtime_state));
var next_hud = (function (){var idx = 0;
var lh = last_hud;
while(true){
if((idx >= 4))
{return lh;
} else
{var p = cljs.core.get_in.call(null,state,cljs.core.PersistentVector.fromArray(["\uFDD0:players",idx], true));
var dom_p = cljs.core.nth.call(null,dom_players,idx);
var hud_div = (new cljs.core.Keyword("\uFDD0:hud-div")).call(null,dom_p);
if(cljs.core.truth_((new cljs.core.Keyword("\uFDD0:active")).call(null,p)))
{var curr_hud_state = cljs.core.PersistentArrayMap.fromArray(["\uFDD0:active",true,"\uFDD0:alive",(new cljs.core.Keyword("\uFDD0:alive")).call(null,p),"\uFDD0:score",(new cljs.core.Keyword("\uFDD0:score")).call(null,p),"\uFDD0:health",(new cljs.core.Keyword("\uFDD0:health")).call(null,p),"\uFDD0:keys",(new cljs.core.Keyword("\uFDD0:keys")).call(null,p),"\uFDD0:bombs",(new cljs.core.Keyword("\uFDD0:bombs")).call(null,p)], true);
var last_hud_p = cljs.core.get.call(null,lh,idx);
if(cljs.core._EQ_.call(null,curr_hud_state,last_hud_p))
{{
var G__3546 = (idx + 1);
var G__3547 = lh;
idx = G__3546;
lh = G__3547;
continue;
}
} else
{if(cljs.core.truth_(hud_div))
{hud_div.style.display = "block";
} else
{}
var score_el = (new cljs.core.Keyword("\uFDD0:score-el")).call(null,dom_p);
var health_el = (new cljs.core.Keyword("\uFDD0:health-el")).call(null,dom_p);
var keys_el = (new cljs.core.Keyword("\uFDD0:keys-el")).call(null,dom_p);
var bombs_el = (new cljs.core.Keyword("\uFDD0:bombs-el")).call(null,dom_p);
if((function (){var or__3943__auto__ = (last_hud_p == null);
if(or__3943__auto__)
{return or__3943__auto__;
} else
{return cljs.core.not_EQ_.call(null,(new cljs.core.Keyword("\uFDD0:score")).call(null,curr_hud_state),(new cljs.core.Keyword("\uFDD0:score")).call(null,last_hud_p));
}
})())
{if(cljs.core.truth_(score_el))
{score_el.textContent = [cljs.core.str((new cljs.core.Keyword("\uFDD0:score")).call(null,p))].join('');
} else
{}
} else
{}
if((function (){var or__3943__auto__ = (last_hud_p == null);
if(or__3943__auto__)
{return or__3943__auto__;
} else
{var or__3943__auto____$1 = cljs.core.not_EQ_.call(null,(new cljs.core.Keyword("\uFDD0:health")).call(null,curr_hud_state),(new cljs.core.Keyword("\uFDD0:health")).call(null,last_hud_p));
if(or__3943__auto____$1)
{return or__3943__auto____$1;
} else
{return cljs.core.not_EQ_.call(null,(new cljs.core.Keyword("\uFDD0:alive")).call(null,curr_hud_state),(new cljs.core.Keyword("\uFDD0:alive")).call(null,last_hud_p));
}
}
})())
{if(cljs.core.truth_(health_el))
{var h_3548 = (new cljs.core.Keyword("\uFDD0:health")).call(null,p);
health_el.textContent = (cljs.core.truth_((new cljs.core.Keyword("\uFDD0:alive")).call(null,p))?[cljs.core.str(h_3548)].join(''):"DEAD");
health_el.style.color = (cljs.core.truth_((new cljs.core.Keyword("\uFDD0:alive")).call(null,p))?(((h_3548 < 30))?"orange":"white"):"red");
} else
{}
} else
{}
if((function (){var or__3943__auto__ = (last_hud_p == null);
if(or__3943__auto__)
{return or__3943__auto__;
} else
{return cljs.core.not_EQ_.call(null,(new cljs.core.Keyword("\uFDD0:keys")).call(null,curr_hud_state),(new cljs.core.Keyword("\uFDD0:keys")).call(null,last_hud_p));
}
})())
{if(cljs.core.truth_(keys_el))
{keys_el.textContent = [cljs.core.str((new cljs.core.Keyword("\uFDD0:keys")).call(null,p))].join('');
} else
{}
} else
{}
if((function (){var or__3943__auto__ = (last_hud_p == null);
if(or__3943__auto__)
{return or__3943__auto__;
} else
{return cljs.core.not_EQ_.call(null,(new cljs.core.Keyword("\uFDD0:bombs")).call(null,curr_hud_state),(new cljs.core.Keyword("\uFDD0:bombs")).call(null,last_hud_p));
}
})())
{if(cljs.core.truth_(bombs_el))
{bombs_el.textContent = [cljs.core.str((new cljs.core.Keyword("\uFDD0:bombs")).call(null,p))].join('');
} else
{}
} else
{}
{
var G__3549 = (idx + 1);
var G__3550 = cljs.core.assoc.call(null,lh,idx,curr_hud_state);
idx = G__3549;
lh = G__3550;
continue;
}
}
} else
{var curr_hud_state = cljs.core.PersistentArrayMap.fromArray(["\uFDD0:active",false], true);
var last_hud_p = cljs.core.get.call(null,lh,idx);
if(cljs.core._EQ_.call(null,curr_hud_state,last_hud_p))
{{
var G__3551 = (idx + 1);
var G__3552 = lh;
idx = G__3551;
lh = G__3552;
continue;
}
} else
{if(cljs.core.truth_(hud_div))
{hud_div.style.display = "none";
} else
{}
{
var G__3553 = (idx + 1);
var G__3554 = cljs.core.assoc.call(null,lh,idx,curr_hud_state);
idx = G__3553;
lh = G__3554;
continue;
}
}
}
}
break;
}
})();
if(cljs.core.not_EQ_.call(null,next_hud,last_hud))
{return cljs.core.swap_BANG_.call(null,dandy.runtime_state,cljs.core.assoc,"\uFDD0:last-hud-state",next_hud);
} else
{return null;
}
});
dandy.compute_keyboard_input = (function compute_keyboard_input(keys,config){
var up = ((cljs.core.contains_QMARK_.call(null,keys,(new cljs.core.Keyword("\uFDD0:up")).call(null,config)))?dandy.kButtonUp:0);
var down = ((cljs.core.contains_QMARK_.call(null,keys,(new cljs.core.Keyword("\uFDD0:down")).call(null,config)))?dandy.kButtonDown:0);
var left = ((cljs.core.contains_QMARK_.call(null,keys,(new cljs.core.Keyword("\uFDD0:left")).call(null,config)))?dandy.kButtonLeft:0);
var right = ((cljs.core.contains_QMARK_.call(null,keys,(new cljs.core.Keyword("\uFDD0:right")).call(null,config)))?dandy.kButtonRight:0);
var fire = ((cljs.core.contains_QMARK_.call(null,keys,(new cljs.core.Keyword("\uFDD0:fire")).call(null,config)))?dandy.kButtonFire:0);
var bomb = ((cljs.core.contains_QMARK_.call(null,keys,(new cljs.core.Keyword("\uFDD0:bomb")).call(null,config)))?dandy.kButtonBomb:0);
return (((((up | down) | left) | right) | fire) | bomb);
});
dandy.poll_gamepad_input = (function poll_gamepad_input(gamepad_idx){
var gamepads = ((typeof navigator !== 'undefined')?navigator.getGamepads():null);
var gp = (cljs.core.truth_(gamepads)?(gamepads[gamepad_idx]):null);
if((gp == null))
{return 0;
} else
{var axes = gp.axes;
var buttons = gp.buttons;
var ax = (((axes.length > 0))?(axes[0]):0.0);
var ay = (((axes.length > 1))?(axes[1]):0.0);
var left = (((ax < -0.5))?dandy.kButtonLeft:0);
var right = (((ax > 0.5))?dandy.kButtonRight:0);
var up = (((ay < -0.5))?dandy.kButtonUp:0);
var down = (((ay > 0.5))?dandy.kButtonDown:0);
var fire_btn = (((buttons.length > 0))?(buttons[0]):null);
var fire = (cljs.core.truth_((function (){var and__3941__auto__ = fire_btn;
if(cljs.core.truth_(and__3941__auto__))
{return fire_btn.pressed;
} else
{return and__3941__auto__;
}
})())?dandy.kButtonFire:0);
var bomb_btn = (((buttons.length > 1))?(buttons[1]):null);
var bomb = (cljs.core.truth_((function (){var and__3941__auto__ = bomb_btn;
if(cljs.core.truth_(and__3941__auto__))
{return bomb_btn.pressed;
} else
{return and__3941__auto__;
}
})())?dandy.kButtonBomb:0);
return (((((left | right) | up) | down) | fire) | bomb);
}
});
dandy.apply_inputs_to_state = (function apply_inputs_to_state(state,keys){
var p1_mask = dandy.compute_keyboard_input.call(null,keys,cljs.core.nth.call(null,dandy.kKeyboardInputConfigs,0));
var p2_mask = dandy.compute_keyboard_input.call(null,keys,cljs.core.nth.call(null,dandy.kKeyboardInputConfigs,1));
var p3_mask = dandy.poll_gamepad_input.call(null,0);
var p4_mask = dandy.poll_gamepad_input.call(null,1);
return cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,cljs.core.assoc_in.call(null,state,cljs.core.PersistentVector.fromArray(["\uFDD0:players",0,"\uFDD0:input-mask"], true),p1_mask),cljs.core.PersistentVector.fromArray(["\uFDD0:players",1,"\uFDD0:input-mask"], true),p2_mask),cljs.core.PersistentVector.fromArray(["\uFDD0:players",2,"\uFDD0:input-mask"], true),p3_mask),cljs.core.PersistentVector.fromArray(["\uFDD0:players",3,"\uFDD0:input-mask"], true),p4_mask);
});
dandy.game_loop = (function game_loop(){
var dom = (new cljs.core.Keyword("\uFDD0:dom-elements")).call(null,cljs.core.deref.call(null,dandy.runtime_state));
var canvas = (new cljs.core.Keyword("\uFDD0:canvas")).call(null,dom);
cljs.core.swap_BANG_.call(null,dandy.runtime_state,(function (s){
var gs_SINGLEQUOTE_ = dandy.apply_inputs_to_state.call(null,(new cljs.core.Keyword("\uFDD0:game-state")).call(null,s),(new cljs.core.Keyword("\uFDD0:pressed-keys")).call(null,s));
var gs_SINGLEQUOTE__SINGLEQUOTE_ = dandy.step_game.call(null,gs_SINGLEQUOTE_);
return cljs.core.assoc.call(null,s,"\uFDD0:game-state",gs_SINGLEQUOTE__SINGLEQUOTE_);
}));
var state = (new cljs.core.Keyword("\uFDD0:game-state")).call(null,cljs.core.deref.call(null,dandy.runtime_state));
dandy.draw_game.call(null,canvas,dandy.assets.strike,state);
dandy.update_hud.call(null,state);
if(cljs.core.truth_(dandy.can_sleep_QMARK_.call(null,state)))
{cljs.core.swap_BANG_.call(null,dandy.runtime_state,cljs.core.assoc,"\uFDD0:is-sleeping",true,"\uFDD0:anim-frame-id",null);
var interval_id = setInterval((function (){
var p3 = dandy.poll_gamepad_input.call(null,0);
var p4 = dandy.poll_gamepad_input.call(null,1);
if((function (){var or__3943__auto__ = cljs.core.not_EQ_.call(null,p3,0);
if(or__3943__auto__)
{return or__3943__auto__;
} else
{return cljs.core.not_EQ_.call(null,p4,0);
}
})())
{return dandy.wake_up_loop_BANG_.call(null);
} else
{return null;
}
}),100);
return cljs.core.swap_BANG_.call(null,dandy.runtime_state,cljs.core.assoc,"\uFDD0:gamepad-poll-interval",interval_id);
} else
{var interval_3555 = (new cljs.core.Keyword("\uFDD0:gamepad-poll-interval")).call(null,cljs.core.deref.call(null,dandy.runtime_state));
if(cljs.core.truth_(interval_3555))
{clearInterval(interval_3555);
cljs.core.swap_BANG_.call(null,dandy.runtime_state,cljs.core.assoc,"\uFDD0:gamepad-poll-interval",null);
} else
{}
return cljs.core.swap_BANG_.call(null,dandy.runtime_state,cljs.core.assoc,"\uFDD0:anim-frame-id",window.requestAnimationFrame(game_loop));
}
});
dandy.wake_up_loop_BANG_ = (function wake_up_loop_BANG_(){
if(cljs.core.truth_((new cljs.core.Keyword("\uFDD0:is-sleeping")).call(null,cljs.core.deref.call(null,dandy.runtime_state))))
{cljs.core.swap_BANG_.call(null,dandy.runtime_state,cljs.core.assoc,"\uFDD0:is-sleeping",false);
return cljs.core.swap_BANG_.call(null,dandy.runtime_state,cljs.core.assoc,"\uFDD0:anim-frame-id",window.requestAnimationFrame(dandy.game_loop));
} else
{return null;
}
});
dandy.cache_dom_elements_BANG_ = (function cache_dom_elements_BANG_(){
return cljs.core.swap_BANG_.call(null,dandy.runtime_state,cljs.core.assoc,"\uFDD0:dom-elements",cljs.core.PersistentArrayMap.fromArray(["\uFDD0:canvas",document.getElementById("gameCanvas"),"\uFDD0:players",cljs.core.vec.call(null,cljs.core.map.call(null,(function (idx){
return cljs.core.PersistentArrayMap.fromArray(["\uFDD0:hud-div",document.getElementById([cljs.core.str("player-hud-"),cljs.core.str(idx)].join('')),"\uFDD0:score-el",document.getElementById([cljs.core.str("p"),cljs.core.str(idx),cljs.core.str("-score")].join('')),"\uFDD0:health-el",document.getElementById([cljs.core.str("p"),cljs.core.str(idx),cljs.core.str("-health")].join('')),"\uFDD0:keys-el",document.getElementById([cljs.core.str("p"),cljs.core.str(idx),cljs.core.str("-keys")].join('')),"\uFDD0:bombs-el",document.getElementById([cljs.core.str("p"),cljs.core.str(idx),cljs.core.str("-bombs")].join(''))], true);
}),cljs.core.range.call(null,4))),"\uFDD0:hud-container",document.getElementById("hud")], true));
});
dandy.start_game = (function start_game(){
dandy.cache_dom_elements_BANG_.call(null);
window.addEventListener("keydown",(function (e){
cljs.core.swap_BANG_.call(null,dandy.runtime_state,cljs.core.update_in,cljs.core.PersistentVector.fromArray(["\uFDD0:pressed-keys"], true),cljs.core.conj,e.code);
return dandy.wake_up_loop_BANG_.call(null);
}),false);
window.addEventListener("keyup",(function (e){
return cljs.core.swap_BANG_.call(null,dandy.runtime_state,cljs.core.update_in,cljs.core.PersistentVector.fromArray(["\uFDD0:pressed-keys"], true),cljs.core.disj,e.code);
}),false);
return cljs.core.swap_BANG_.call(null,dandy.runtime_state,cljs.core.assoc,"\uFDD0:anim-frame-id",window.requestAnimationFrame(dandy.game_loop));
});
window.addEventListener("load",dandy.start_game,false);
