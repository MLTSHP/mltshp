function straw() {
    this.morsels = new Array();
    this.id = 0;
  
    this.init = function(){
        var head = document.getElementsByTagName('head')[0],
        style = document.createElement('style'),
        rules = document.createTextNode('div#mltshp_container div.chum_overlay{border:10px solid #ede500;cursor:pointer;font-family:Arial,Helvetica,sans-serif;font-size:16px;font-weight:bold;padding:10px;position:absolute;z-index:5000000;}\ndiv#mltshp_container div.chum_overlay div{background:#ede500;color:#000;padding:10px;text-align:center;}\ndiv#mltshp_container div.chum_overlay:hover{border:10px solid #f6ff00;}\ndiv#mltshp_container div.chum_overlay div:hover{background:#f6ff00;}');
        style.type = 'text/css';

        if(style.styleSheet)
        {
            style.styleSheet.cssText = rules.nodeValue;
        } else {
            style.appendChild(rules);
        }
        head.appendChild(style);

        // set up page overlay for the morsels.
        var container = document.createElement("div");
        container.id = "mltshp_container";
        document.getElementsByTagName("body")[0].appendChild(container);
        document.getElementById("mltshp_container").style.display = "none";
        this.chum_chum();
    }

    this.chum_chum = function(){
      
        // first they came for the images
        var images = document.getElementsByTagName("img");
        for(var i = 0;i<images.length;i++){
            var image = images[i];

            if (image.offsetWidth >= 100 && image.offsetHeight >= 100 && image.src != ''){
                var width = image.offsetWidth;
                var height = image.offsetHeight;
                var pos = this.media_location(image);
                this.create_overlay('image', width, height, pos, this.id, image.src);
            }
            this.id++;
        }
      
        // then they came for the youtube videos
        //if (document.domain == "youtube.com" || document.domain == "localhost" || document.domain == "www.youtube.com"){
        if (false){
            player_holder = document.getElementById('watch-player');
            nodes = player_holder.childNodes;
            for(var k=0;k<nodes.length;k++){
                this_node = nodes[k]
                if((this_node.nodeName) === "IFRAME"){
                    var width = this_node.offsetWidth;
                    var height = this_node.offsetHeight;
                    var pos = this.media_location(this_node);
                    this.create_overlay('video', width, height, pos, this.id, location.href);
                    this.id++;
                    break;
                }
            }
        }
        
        // then they came for the vimeo videos
        //if (document.domain == "vimeo.com" || document.domain == "localhost" || document.domain == "www.vimeo.com"){
        if (false){
            possible_players = document.getElementsByTagName('div');

            for(var j = 0;j<possible_players.length;j++){
                if(typeof(possible_players[j]) === "object"){
                    if(possible_players[j].className == "vimeo_holder"){
                        var width = possible_players[i].offsetWidth;
                        var height = possible_players[i].offsetHeight;
                        var pos = this.media_location(possible_players[j]);
                        this.create_overlay('video', width, height, pos, this.id, location.href);
                        this.id++;
                    }
                }
            }
            
        }
    }
  
    this.create_overlay = function(type, width, height, pos, obj_id, url){
        var overlay = document.createElement("div");
        overlay.id = "chum_overlay_" + obj_id;
        overlay.setAttribute("class", "chum_overlay");
        overlay.style.display = "block";
        overlay.style.width = (width - 40) + "px";
        overlay.style.height = (height - 40) + "px";
        overlay.style.left = pos[0] + "px";
        overlay.style.top = pos[1] + "px";
        overlay.innerHTML = "<div id='chum_inner_" + obj_id + "'>save this " + type + "</div>";
        if(type == "image"){
            overlay.setAttribute("onclick", "straw.select_image('" + url + "')");
        } else if(type=="video"){
            overlay.setAttribute("onclick", "straw.select_video('" + url + "')");
        }
        document.getElementById("mltshp_container").appendChild(overlay);
    }
  
    this.media_location = function(media_object){
        var x = media_object.offsetLeft;
        var y = media_object.offsetTop;

        while (media_object.offsetParent) {
            x = x + media_object.offsetParent.offsetLeft;
            y = y + media_object.offsetParent.offsetTop;

            if (media_object == document.getElementsByTagName("body")[0]) {
                break;
            } else {
                media_object = media_object.offsetParent;
            }
        }
        return [x, y];
    }

    this.select_image = function(image_url){
        //open a new window
        //location is 
        left_location = screen.width/2-450;
        top_location = screen.height/2-300;
        var window_attributes = "width=850,height=650,menubar=yes,toolbar=yes,scrollbars=yes,resizable=yes,left=" + left_location + ",top=" + top_location + "screenX=" + left_location + ",screenY=" + top_location;
        window.open('http://mltshp.com/tools/p?url=' + escape(image_url) + '&source_url=' + escape(location.href) ,'save image',window_attributes);
    }

    this.select_video = function(video_url){
        console.log(video_url);
    }

  this.init();
  document.getElementById("mltshp_container").style.display = "block";
}

if(!window.straw_running) {
    window.straw_running = true;
    var straw = new straw();
} else {
    document.getElementById("mltshp_container").style.display = "none";
    window.straw_running = false;
    d = document.getElementsByTagName("body")[0]
    dd = document.getElementById('mltshp_container');
    d.removeChild(dd);
}
