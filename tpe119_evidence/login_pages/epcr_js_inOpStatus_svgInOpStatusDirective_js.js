app.directive('svgInOpStatus', ['$window','$compile', function ($window,$compile) {
    
  return {
      restrict: 'A',
      scope: {
        opStatus: "=",
        opExtra: "=",
        opPreStatus: "=",
        refreshStatus: "=",
        extraOnClick: "&",
        statusOnClick: "&"       // 點到各狀態觸發
      },
      templateUrl: 'templates/inOpStatus/inOpStatus.svg',
  link: function (scope, element, attrs) {
      var opExtra = [];   // FeatureAdd 2019-10-23 用來呈現額外的資訊(按鈕)在狀態列後面，目前用來呈現插管狀態
      var  opStatus = [];
      var opPreStatus = [];   //[{title: "qoo", time: "99:99", id: 95, code: "8888"}];
      var  s_svg       = document.getElementById("op-status");
      var  svgns       = "http://www.w3.org/2000/svg";
      var  xlinkns     = "http://www.w3.org/1999/xlink";

      var resizeWindow = function(){
        var newwidth = $window.innerWidth;
        // FeatureChange Jordan 2019-11-01 動態縮小，要不能畫面縮小會點不到
        if(s_svg && s_svg.style){
          s_svg.style.width = newwidth;
          s_svg.viewBox = "0 0 " + newwidth + " 68";
        }
        // var  vbox_str = "" + 0 + " " + 0 + " 1440 68"
        // s_svg.setAttributeNS(null,"viewBox",vbox_str);
        // s_svg.setAttributeNS(null,"preserveAspectRatio","xMidYMid meet");
      }

      angular.element($window).on('resize', function () {
        resizeWindow();
      });

      scope.$watch('opStatus', function(newValue, oldValue) {
        if (newValue){
          // Jordan 2017-10-02 因為似乎不是指到同一個記憶體位址，所以要再指定給它一次
          opStatus = scope.opStatus;  // 其實此時的 scope.vitalData 會等於 newValue
          // console.log('@@@@@@@@@@@@@@@ GOT opStatus @@@@@@@@@@@@@@@');
        }
      }, true);

      scope.$watch('opExtra', function(newValue, oldValue) {
        if (newValue){
          // Jordan 2017-10-02 因為似乎不是指到同一個記憶體位址，所以要再指定給它一次
          opExtra = scope.opExtra;  // 其實此時的 scope.vitalData 會等於 newValue
          // console.log('@@@@@@@@@@@@@@@ GOT opStatus @@@@@@@@@@@@@@@');
        }
      }, true);

      scope.$watch('opPreStatus', function(newValue, oldValue) {
        if (newValue){
          opPreStatus = scope.opPreStatus;
        }
      }, true);

      scope.$watch('refreshStatus', function(newValue, oldValue) {
        if (newValue != 'undefined' && newValue != null){
          
          // console.log('@@@@@@@@@@@@@@@ drawStatusBar(); @@@@@@@@@@@@@@@')
          // drawStatusBar();
          setupSVG(s_svg);
          resizeWindow();
        }
      }, true);

      // opExtra[0] = {"title":"插管(15:30)","badge": 3,"opMainId": 3, "action": "in"};
      // opExtra[1] = {"title":"拔管","badge": 1,"opMainId": 3, "action": ""};

      /* current = 1 state will blink and the color is green */
      /* endshape =1 state is marked by a rectangular shape */
      /* there is no output arrow from the last state of the array */
       // -- chinese version for testing
         // opStatus[0] = {"title":"報到","time":"11:05","current":"0","endshape":"0"};
         // opStatus[1] = {"title":"sign in","time":"11:10","current":"0","endshape":"0"};
         // opStatus[2] = {"title":"麻醉開始","time":"11:20","current":"0","endshape":"0"};
         // opStatus[3] = {"title":"Time out","time":"11:30","current":"0","endshape":"0"};
         // opStatus[4] = {"title":"手術開始","time":"11:35","current":"0","endshape":"0"};
         // opStatus[5] = {"title":"結束前30分","time":"11:55","current":"1","endshape":"1"};

         // opStatus[6] = {"title":"手術結束","time":"12:25","current":"0","endshape":"0"};
         // opStatus[7] = {"title":"sign out","time":"12:30","current":"0","endshape":"0"};
         // opStatus[8] = {"title":"麻醉結束","time":"12:40","current":"0","endshape":"0"};
         // opStatus[9] = {"title":"離開術房","time":"12:50","current":"1","endshape":"1"};
      
      /* -- english version of status */
         // opStatus[0] = {"title":"Report in","time":"11:05","current":"0","endshape":"0"};
         // opStatus[1] = {"title":"Sign in","time":"11:10","current":"0","endshape":"0"};
         // opStatus[2] = {"title":"Start Anes.","time":"11:20","current":"0","endshape":"0"};
         // opStatus[3] = {"title":"Time out","time":"11:30","current":"0","endshape":"0"};
         // opStatus[4] = {"title":"Start Op.","time":"11:35","current":"0","endshape":"0"};
         // opStatus[5] = {"title":"30min To End","time":"11:55","current":"0","endshape":"0"};
         // opStatus[6] = {"title":"End of Op","time":"12:25","current":"0","endshape":"0"};
         // opStatus[7] = {"title":"sign out","time":"12:30","current":"0","endshape":"0"};
         // opStatus[8] = {"title":"End of Anes.","time":"12:40","current":"1","endshape":"0"};
         // opStatus[9] = {"title":"Left Op room","time":"12:50","current":"0","endshape":"0"};

      /* ================================================================================= */
      // =========================================================================================== 
      /*               Parameters for display
      // ----------------------------------------------------------
      //  svg   id = op-info        width = 1100 height = 80
      //  svg   id = op-status      width = 1100 height = 60
      //  svg   id = tmline-legend  width = 150 height = 1500
          svg   id = op-timeline    width = 800 height = 1500
          svg   id = op-rightmenu   width = 138 height = 1500
      */

      //  DisplayWidth  is width of screen, divided by width of tmline-legend, op-timeline and op-rightmenu
      var DisplayWidth  = 1440;
      var InfoHeight    = 110; /* Height of Information contents */
      var StatusHeight  = 68; /* Height of Status bar 原 68 */
      // var ContentHeight = 1500; //  ContentHeight is the height of all contents in op-timeline
      // var LeftWidth     = 150;
      // var CenterWidth   = 800;
      // var RightWidth    = DisplayWidth - (LeftWidth + CenterWidth + 12);
      // var FloatHeight   = 50;

      /* ------------ Status Box ------------------------------- */
      /*   要改變 狀態中文字顏色 或 顯示的顏色與底色，在 style 中設定 
          .state { fill: #c8c8c8; 
          .state text { color: black; }
          .state:hover, .state:focus { fill: red; }
          .state:hover text, .state:focus text { fill: red; }
          @keyframes status-current { 0%, 10%  {opacity: 0.3} 25%, 85% {opacity: 0.9;fill:green;} 100%     {opacity: 0.3} }
      */
      var StateBoxHeight       = 70; // ph in oneState()   
      var StateBoxRectWidth    = 100; // pw in oneState()  
      var StateExtraWidth    = 140; // pw in oneState()
      var StateBoxTriangleX    = 15; // pdx in oneState()  
      var StatusUpperLeftX     = 5; // upper left corner position of start state  
      var StatusUpperLeftY     = 0; // upper left corner position of start state  
      var StateGap             = 15; // State to State distance (StateBoxRectWidth + StateBoxTriangleX + StateGap) 
      var StateExtraGap             = 5;
      
      /* ================================== 設定各顯示區域的寬與高 */
      function setupSVG(s_svg) {
        s_svg.style.width = DisplayWidth; s_svg.style.height = StatusHeight;
        var statusStartX = 0;

        if(opPreStatus && opPreStatus.length != 0){
          var preStatus = drawOpPreStatus();
          statusStartX = preStatus.statusEndX + StateExtraGap*4;
        }

        var info = drawStatusBar(statusStartX);
        var param = {};
        param.x = info.statusEndX + StateExtraGap*4;  // 希望的起點
        param.y = info.statusEndY;
        drawExtraInfo(param);
      }

      // =================== setup SVG panel sizes and <g> tags for each display panel
      editStatus = function (evt,title,fullTime,checkPointId,checkPointCode) {
        scope.statusOnClick(
          {
            arg:{
                'label':title,
                'fullTime':fullTime,
                'checkPointId':checkPointId,
                'checkPointCode':checkPointCode   // go identify which status, this should be pass in via ...
            }
          }
        )
      }

      extraOnClick = function (evt,opMainId,badge,title,action,jsonData) {
        // console.log('============== ON CLICK:',opMainId,badge,title,action,jsonData)
        scope.extraOnClick(
          {
            arg:{
                'opMainId': opMainId,
                'badge': badge,
                'title': title,
                'action': action,
                'data': jsonData
            }
          }
        )
      }


      /* ----------------------------- */
      /* 
      var StateBoxHeight    = 40; / ph in oneState()  /
      var StateBoxRectWidth = 70; / pw in oneState()  /
      var StateBoxTriangleX = 15; / pdx in oneState() /
      var StatusUpperLeftX  = 160; / upper left corner position of start state /
      var StatusUpperLeftY  = 10;  upper left corner position of start state /
      var StateGap          = 10; State to State distance (StateBoxRectWidth + StateBoxTriangleX + StateGap) 
      */
      // 若 DisplayWidth 小於 cnt * s2s_dist 
      //.   往下方開啟另一列 
      //    StatusHeight 必須大於 2*StateBoxHeight + vgap
      function drawStatusBar(startX) {
// console.log('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ drawStatusBar')
        var sx=startX,sy=StatusUpperLeftY; /* upper left corner position of start state */
        var wd=(StateBoxRectWidth+StateBoxTriangleX),mid_h=(StateBoxHeight/2); /* gap: dist between two states, wd=pw+pdx in oneState() */
        var cnt=opStatus.length,seg_cnt,vgap=10;
        var cx=sx,cy=sy,s2s_dist=(StateBoxRectWidth + StateBoxTriangleX + StateGap);
        var cObj,dirR=1;
        // if(DisplayWidth < (sx+cnt*s2s_dist) ) {
        //   // 自動折行的能力，但目前寬度是訂死的，要能動態得到視窗的寬度才能呈現的更完美
        //   seg_cnt = Math.floor( (DisplayWidth-sx)/s2s_dist ) - 1;
        //   for(var i=0;i<cnt;i++) {
        //     cObj=opStatus[i];
        //     oneState(s_svg,cx,cy,cObj.title,cObj.time,cObj.current,cObj.endshape,dirR,cObj.id,cObj.code,cObj.fullTime, cObj.isDefaultSeq, cObj.badge);
        //     if(i == seg_cnt ) {
        //        drawContinueArrowLine(s_svg,cx+wd,cy+mid_h,cx+wd,cy+mid_h+StateBoxHeight+vgap);
        //        cx += wd; cy += StateBoxHeight+vgap;
        //        dirR = 0;
        //     } else if (i > seg_cnt) {
        //        if(i < (cnt-1)) { drawArrowLine(s_svg,cx-wd,cy+mid_h,cx-s2s_dist,cy+mid_h); }
        //        cx -= s2s_dist;
        //     } else {
        //        if(i < (cnt-1)) { drawArrowLine(s_svg,cx+wd,cy+mid_h,cx+s2s_dist,cy+mid_h); }
        //        cx += s2s_dist;
        //     }
        //   }
        // } else {
          for(var i=0;i<cnt;i++) {
            cObj=opStatus[i];
            oneState(s_svg,cx,cy,cObj.title,cObj.time,cObj.current,cObj.endshape,dirR,cObj.id,cObj.code,cObj.fullTime, cObj.isDefaultSeq, cObj.badge);
            // if(i < (cnt-1)) { drawArrowLine(s_svg,cx+wd,cy+mid_h,cx+s2s_dist,cy+mid_h); }
            if(i<(cnt-1)) { drawArrow(s_svg,cx+wd,cy+mid_h)}
            cx += s2s_dist; 
          }
        // }
        
        // 扣掉最後一個 state 的間隙，我想要的是貼在最後一階段屁股的 X
        cx = cx - StateGap;

        return {'statusEndX': cx, 'statusEndY': cy}
      }

      /* ------------------------------------------------ */
      function drawArrow(v_svg,x1,y1){
        var use = document.createElementNS(svgns, "use");
        use.setAttributeNS(xlinkns, "id", "_arrowIcon");
        // 取得符號
        use.setAttributeNS(xlinkns, "href", "#mkArrow");
        use.setAttributeNS(null,"y", y1);      // 後面加的數字都是客製的
        use.setAttributeNS(null,"x", x1);  // 後面加的數字都是客製的
        v_svg.appendChild(use);

      }

      /* from one state to next state */
      function drawArrowLine(v_svg,x1,y1,x2,y2) {
          var hgap=6; /* room for arrow head */
          var lineElem = document.createElementNS(svgns, "line");
            lineElem.setAttributeNS(null,"x1",x1); lineElem.setAttributeNS(null,"y1",y1);
            if(x2>x1) { lineElem.setAttributeNS(null,"x2",x2-hgap); }
                 else { lineElem.setAttributeNS(null,"x2",x2+hgap); }
            lineElem.setAttributeNS(null,"y2",y2);
            lineElem.setAttributeNS(null,"style","stroke:#c8c8c8;stroke-width:3");
            lineElem.setAttributeNS(null,"marker-start","url(#mkCircle)");
            lineElem.setAttributeNS(null,"marker-end","url(#mkArrow)");
            v_svg.appendChild(lineElem);
      }

      /* from one state to next state */
      function drawContinueArrowLine(v_svg,x1,y1,x2,y2) {
          var hgap=6; /* room for arrow head */
          var hext=12;
          var lineElem = document.createElementNS(svgns, "polyline");
          var p=[],p_str;
          p[0] = ''+x1+','+y1;        p[1] = ''+(x1+hext)+','+y1;
          p[2] = ''+(x1+hext)+','+y2; p[3] = ''+(x2+hgap)+','+y2;
          p_str=p.join(' ');
            lineElem.setAttributeNS(null,"points",p_str);
            lineElem.setAttributeNS(null,"style","fill:none;stroke:#c8c8c8;stroke-width:3");
            lineElem.setAttributeNS(null,"marker-start","url(#mkCircle)");
            lineElem.setAttributeNS(null,"marker-end","url(#mkArrow)");
            v_svg.appendChild(lineElem);
      }

      function renewGelementById(g_id) {
        // var gElem = $(document.getElementById(g_id));
        var gElem = document.getElementById(g_id);
        // if( gElem.length > 0 ) { 
        if( gElem != null && gElem != 'undefined')
        {
          // gElem.empty(); 
          while (gElem.firstChild) {
            gElem.removeChild(gElem.firstChild);
          }
          // console.log('=============================================== DELETED')
        } else { 
            gElem = document.createElementNS(svgns, "g");
            gElem.setAttributeNS(null,"id",g_id);
            // gElem = angular.element(gElem);
            // console.log('=============================================== CREATED')
        }
        return gElem;
      }
      /* ------------------------------------------------ */
      /* x, y upper left corner of state polygon */
      /* t_str1 state title */
      /* t_str2 time string */
      /* isC string "1" indicates current state */
      /* isE string "1" indicates state shape as rect */
      function oneState(v_svg,x,y,t_str1,t_str2,isC,isE,dirR,checkPointId,checkPointCode,fullTime,isDefaultSeq, badge) {
          var  ph=StateBoxHeight, pw=StateBoxRectWidth,pdx=StateBoxTriangleX; /* ph: height of polygon, pw: width of inner polygon rectangle */
          var  p=[]; /* store 5-point coords of state polygon, each point is a string "x,y" */
          var  p_str; /* path string */
          var  plyElem  = document.createElementNS(svgns, "polygon");
          var  tx,ty,tdy;///* middle of title string position */
          var textStyle;

          if(isDefaultSeq && isDefaultSeq == true){
            textStyle = "fill:black;stroke:none;"
          }else{
            textStyle = "fill:#c2325b;stroke:none;"
          }

          // Jordan 2018-01-16
          var  g_id   = "gId_" + checkPointId ;
          p[0]= ''+x+','+y;
          if(dirR==1) {
            if(isE == "1") {
              p[1]= ''+(x+pw+pdx/2)+','+y; p[2]= ''+(x+pw+pdx/2)+','+(y+ph);
              p[4]= ''+x+','+(y+ph);
              plyElem.setAttributeNS(null,"stroke","none");plyElem.setAttributeNS(null,"stroke-width","3px");
            } else {
              p[1]= ''+(x+pw)+','+y;       p[2]= ''+(x+pw+pdx)+','+(y+ph/2);
              p[3]= ''+(x+pw)+','+(y+ph);  p[4]= ''+x+','+(y+ph);
            }
            tx= x + pw/2 + pdx/3, ty = y + ph/2-8, tdy=17;
          } else { // left direction, upper right corder as x0,y0
            if(isE == "1") {
              p[1]= ''+(x-pw-pdx/2)+','+y; p[2]= ''+(x-pw-pdx/2)+','+(y+ph);
              p[4]= ''+x+','+(y+ph);
              plyElem.setAttributeNS(null,"stroke","none");plyElem.setAttributeNS(null,"stroke-width","3px");
            } else {
              p[1]= ''+(x-pw)+','+y;       p[2]= ''+(x-pw-pdx)+','+(y+ph/2);
              p[3]= ''+(x-pw)+','+(y+ph);  p[4]= ''+x+','+(y+ph);
            }
            tx= x - pw/2 - pdx/3, ty = y + ph/2-8, tdy=17; 
          }
          p_str=p.join(' ');
          // var gElem     = document.createElementNS(svgns, "g"); /* <g> tag grouping all things */
          // Jordan 2018-01-16 修正會有殘影的問題
          var gElem = renewGelementById(g_id);

          if(isC == "1") { /* <g> tag attribute indicates current state */
            gElem.setAttributeNS(null,"class","state status-current"); 
          } else {
            gElem.setAttributeNS(null,"class","state"); /* <g> tag attribute */
          }
            plyElem.setAttributeNS(null,"points",p_str);

            var onclick_str = '';
            onclick_str = 'editStatus(evt,\''+ t_str1 +'\',\''+ fullTime +'\',\''+ checkPointId +'\',\''+ checkPointCode +'\')';
            plyElem.setAttributeNS(null,"onclick",onclick_str);

            gElem.appendChild(plyElem); /* place polygon element under <g> tag */
          var txtElem  = document.createElementNS(svgns, "text"); /* title string */
            txtElem.setAttributeNS(null,"x",tx); txtElem.setAttributeNS(null,"y",ty);
            txtElem.setAttributeNS(null,"dy",".35em");
            txtElem.setAttributeNS(null,"text-anchor","middle");
            txtElem.setAttributeNS(null,"style",textStyle);
            txtElem.setAttributeNS(null,"onclick",onclick_str);

          var n_label  = document.createTextNode(t_str1);
            txtElem.appendChild(n_label);
            gElem.appendChild(txtElem); /* place text elements under <g> tag */
          txtElem     = document.createElementNS(svgns, "text"); /* time string */
            txtElem.setAttributeNS(null,"x",tx); txtElem.setAttributeNS(null,"y",ty+tdy);
            txtElem.setAttributeNS(null,"dy",".65em");
            txtElem.setAttributeNS(null,"text-anchor","middle");
            txtElem.setAttributeNS(null,"style",textStyle);
            txtElem.setAttributeNS(null,"onclick",onclick_str);

          n_label     = document.createTextNode(t_str2);
            txtElem.appendChild(n_label);
            gElem.appendChild(txtElem); /* place text elements under <g> tag */
            v_svg.appendChild(gElem);
        if(!_.isNil(badge)) {
          tstyle_str = 'stroke:none;fill:red;font-size:16'
          var txtElemBadge = makeTxtElement({ svgns: v_svg, cx: x+StateBoxRectWidth-15, cy: y+StateBoxHeight-9,
                            txt_anchor: 'Start', style_str: tstyle_str, onclick: 'QQQQQ'})
          txtElemBadge.append(badge);
          gElem.appendChild(txtElemBadge);
          v_svg.appendChild(gElem)
        }
      }

      function onePreState(v_svg,x,y,t_str1,t_str2,checkPointId) {
          var  ph=StateBoxHeight, pw=StateBoxRectWidth,pdx=StateBoxTriangleX; /* ph: height of polygon, pw: width of inner polygon rectangle */
          var  p=[]; /* store 5-point coords of state polygon, each point is a string "x,y" */
          var  p_str; /* path string */
          var  plyElem  = document.createElementNS(svgns, "polygon");
          var  tx,ty,tdy;///* middle of title string position */
          var textStyle;
          
            textStyle = "fill:black;stroke:none;"

          // Jordan 2018-01-16
          var  g_id   = "gId_" + checkPointId ;
          p[0]= ''+x+','+y;

          p[1]= ''+(x+pw+pdx/2)+','+y; p[2]= ''+(x+pw+pdx/2)+','+(y+ph);
          p[4]= ''+x+','+(y+ph);
          // plyElem.setAttributeNS(null,"stroke","#999999");
          // plyElem.setAttributeNS(null,"stroke-width","0px");
        
          tx= x + pw/2 + pdx/3, ty = y + ph/2-8, tdy=17;

          p_str=p.join(' ');

          // Jordan 2018-01-16 修正會有殘影的問題
          var gElem = renewGelementById(g_id);

            gElem.setAttributeNS(null,"class","preState"); /* <g> tag attribute */

            plyElem.setAttributeNS(null,"points",p_str);

            // var onclick_str = '';
            // onclick_str = 'editStatus(evt,\''+ t_str1 +'\',\''+ fullTime +'\',\''+ checkPointId +'\',\''+ checkPointCode +'\')';
            // plyElem.setAttributeNS(null,"onclick",onclick_str);

            gElem.appendChild(plyElem); /* place polygon element under <g> tag */
          var txtElem  = document.createElementNS(svgns, "text"); /* title string */
            txtElem.setAttributeNS(null,"x",tx); txtElem.setAttributeNS(null,"y",ty);
            txtElem.setAttributeNS(null,"dy",".35em");
            txtElem.setAttributeNS(null,"text-anchor","middle");
            txtElem.setAttributeNS(null,"style",textStyle);
            // txtElem.setAttributeNS(null,"onclick",onclick_str);

          var n_label  = document.createTextNode(t_str1);
            txtElem.appendChild(n_label);
            gElem.appendChild(txtElem); /* place text elements under <g> tag */
          txtElem     = document.createElementNS(svgns, "text"); /* time string */
            txtElem.setAttributeNS(null,"x",tx); txtElem.setAttributeNS(null,"y",ty+tdy);
            txtElem.setAttributeNS(null,"dy",".65em");
            txtElem.setAttributeNS(null,"text-anchor","middle");
            txtElem.setAttributeNS(null,"style",textStyle);
            // txtElem.setAttributeNS(null,"onclick",onclick_str);

          n_label     = document.createTextNode(t_str2);
            txtElem.appendChild(n_label);
            gElem.appendChild(txtElem); /* place text elements under <g> tag */
            v_svg.appendChild(gElem);
      }

      function drawOpPreStatus() {
        var sx=StatusUpperLeftX,sy=StatusUpperLeftY; /* upper left corner position of start state */
        var wd=(StateBoxRectWidth),mid_h=(StateBoxHeight/2); /* gap: dist between two states, wd=pw+pdx in oneState() */
        var cnt=opPreStatus.length,seg_cnt,vgap=10;
        var cx=sx,cy=sy,s2s_dist=(StateBoxRectWidth + StateGap);
        var cObj,dirR=1;

        for(var i=0;i<cnt;i++) {
          cObj=opPreStatus[i];
          onePreState(s_svg,cx,cy,cObj.title,cObj.time,cObj.id);
          // if(i < (cnt-1)) { drawArrowLine(s_svg,cx+wd,cy+mid_h,cx+s2s_dist,cy+mid_h); }
          cx += s2s_dist; 
        }
        
        // 扣掉最後一個 state 的間隙，我想要的是貼在最後一階段屁股的 X
        if(cx > sx){
          cx = cx - StateGap;
        }

        return {'statusEndX': cx, 'statusEndY': cy}
      }

      function drawExtraInfo(param) {
        var cx=param.x,cy=param.y,s2s_dist=(StateExtraWidth + StateExtraGap);
        var cObj,dirR=1;

        // BugFix Jordan 2019-10-31 Clear 建立管路，再刪除管路，會有殘留的按鈕
        for(var i = 0; i<2; i++){
          var g_id = "gId_Extra_" + i ;
          renewGelementById(g_id);
        }

        for(var i=0;i<opExtra.length;i++) {
          cObj=opExtra[i];
          var input = {};
          input.x = cx;                     // 按鈕的 X
          input.y = cy;                     // 按鈕的 Y
          input.title = getTitle(cObj.action);         // 按鈕中間的呈現字間
          input.opMainId = cObj.opMainId;   // opMainId
          input.badge = cObj.data.length;         // 按鈕的數字
          input.index = i;                  // 用來做 SVG 的 id 組合
          input.bgColor = getColor(cObj.action);     // 按鈕的背景色
          input.width = StateExtraWidth;    // 按鈕的寬
          input.height = StateBoxHeight;    // 按鈕的高
          input.action = cObj.action;       // '':無特別動作 'in':插管 'ex':拔管 用來點擊之後，讓呼叫的人識別是那一個動作
          input.iconName = getIconName(cObj.action);   // 若需呈現圖示
          input.data = cObj.data;
          oneExtra(s_svg,input);
          cx += s2s_dist;                   // 下一個按鈕的向右位移量
        }
      }

      function getTitle(action){
        if(action == 'in'){
          return '插管';
        }else if(action == 'ex'){
          return '拔管';
        }else if(action == 'toPor'){
          return '轉POR通知'
        }else{
          return '呼吸道評估'; 
        }
      }

      function getColor(action){
        if(action == 'in'){
          return '#E873A8';
        }else if(action == 'ex'){
          return '#00ADB0';
        }else if(action == 'toPor') {
          return '#00c91b'
        }else{
          return '#5CBCE9'; 
        }
      }

      function getIconName(action){
        if(action == 'in'){
          return '#intuIcon';
        }else if(action == 'ex'){
          return '#extuIcon';
        }else{
          return '';
        }
      }

      /* ------------------------------------------------ */
      /* x, y upper left corner of state polygon */
      /* t_str1 state title */
      /* t_str2 time string */
      /* isC string "1" indicates current state */
      /* isE string "1" indicates state shape as rect */
      function oneExtra(v_svg,param) {
          // Jordan 2018-01-16
          var g_id   = "gId_Extra_" + param.index ;
          var tstyle_str='stroke:none;fill:white;';
          var rstyle_str='stroke:none;fill:'+ param.bgColor +';';
          var use;
          var textX;

          param.id = "extraRect_" + param.index;
          param.style = rstyle_str;

          var rectElem = makeRectElement(param);

          // Jordan 2018-01-16 修正會有殘影的問題 -------------------------------
          var gElem = renewGelementById(g_id);
          gElem.setAttributeNS(null,"class","stateExtra");
          var onclick_str = '';
          onclick_str = 'extraOnClick(evt,\''+ param.opMainId +'\',\'' + param.badge + '\',\'' + param.title + '\',\'' + param.action + '\',\'' + JSON.stringify(param.data) + '\')';
          
          // 畫方塊和加點擊事件  ------------------------------------------------
          rectElem.setAttributeNS(null,"onclick",onclick_str);
          gElem.appendChild(rectElem); /* place polygon element under <g> tag */
          v_svg.appendChild(gElem);

          // 判斷是否要呈現圖示
          if(param.iconName && param.iconName != '' && param.iconName != 'undefined'){
            // 呈現圖示
            use = document.createElementNS(svgns, "use");
            use.setAttributeNS(xlinkns, "id", "respIcon_" + param.action + '_' + param.index);
            // 取得符號
            use.setAttributeNS(xlinkns, "href", param.iconName);
            use.setAttributeNS(null,"y", param.y + 18);      // 後面加的數字都是客製的
            use.setAttributeNS(null,"x", param.x + 3);  // 後面加的數字都是客製的
            gElem.appendChild(use);

            textX = param.x + 24 + ((StateExtraWidth-24)/2); // 24 是圖示的寬度  // 因為要置中排，所以計算中心的座標
          }else{
            textX = param.x+(StateExtraWidth/2);  // 因為要置中排，所以計算中心的座標
          }

          // 畫呈現的文字  -----------------------------------------------------
          // 目前設計成最多三排，超過就當作三排，讓它蓋到以下的東西
          var timeStr = '';
          var yOffset = 30; // 預期一個管路時的 y
          var tmpParam = { svgns: svgns, cx: textX, cy: param.y+yOffset,
                                      txt_anchor: 'middle', style_str: tstyle_str,
                                      onclick: onclick_str};
          // FeatureChange 2019-10-31 根據字串長度決定
          var info = getFontSize(param.data);
          var lineNum = 1;
          if(info.maxLen <= 10){
            lineNum = 1;
          }else{
            lineNum = 2;
          }
          if(param.data){
            if(param.data.length == 0){
              var txtElem = makeTxtElement(tmpParam)
              txtElem.append(param.title);
              gElem.appendChild(txtElem); /* place text elements under <g> tag */

            }else if(param.data.length == 1){
              // 調整靠右排列，比較整齊
              
              tmpParam.txt_anchor = 'end';
              tmpParam.cx = param.x + StateExtraWidth - 2;
              tmpParam.style_str = 'stroke:none;fill:white;font-size:' + info.fontSize;
            }else if(param.data.length == 2){
              // 調整靠右排列，比較整齊
              tmpParam.cx = param.x + StateExtraWidth - 2;
              tmpParam.txt_anchor = 'end';

              tmpParam.style_str = 'stroke:none;fill:white;font-size:' + info.fontSize;
              if(lineNum == 1){
                yOffset = 23;
              }else{
                yOffset = 14;
              }
            }else if(param.data.length >= 3){
              // 調整靠右排列，比較整齊
              tmpParam.cx = param.x + StateExtraWidth - 2;
              tmpParam.txt_anchor = 'end';

              tmpParam.style_str = 'stroke:none;fill:white;font-size:' + info.fontSize;
              if(lineNum == 1){
                yOffset = 18;
              }else{
                yOffset = 12;
              }
            }

            for(var i = 0; i < param.data.length ; i++){
              if(i == 0){
                tmpParam.cy = param.y + (yOffset * (i+1));
              }else{
                tmpParam.cy = tmpParam.cy + yOffset;
              }
              if(lineNum == 1){
                tmpParam.cy = param.y + (yOffset * (i+1));
                // 無時間的話，將管路名稱置中放
                if(!param.data[i].time || param.data[i].time == ''){
                  tmpParam.txt_anchor = 'middle';
                  tmpParam.cx = param.x + 24 + (StateExtraWidth - 24)/2;
                }else{
                  tmpParam.txt_anchor = 'end';
                  tmpParam.cx = param.x + StateExtraWidth - 2;
                }

                var txtElem = makeTxtElement(tmpParam)
                txtElem.append(param.data[i].tubeName + ' ' + param.data[i].time);
                gElem.appendChild(txtElem); /* place text elements under <g> tag */
              }else{
                // 2 行
                // 管路名稱置中
                tmpParam.txt_anchor = 'middle';
                tmpParam.cx = param.x + 24 + (StateExtraWidth - 24)/2;
                var txtElem = makeTxtElement(tmpParam)
                txtElem.append(param.data[i].tubeName);
                gElem.appendChild(txtElem); /* place text elements under <g> tag */


                // 時間放在下一行
                // 時間靠右
                tmpParam.txt_anchor = 'end';
                tmpParam.cx = param.x + StateExtraWidth - 2;
                tmpParam.cy = tmpParam.cy + yOffset;
                var txtElem = makeTxtElement(tmpParam)
                txtElem.append(param.data[i].time);
                gElem.appendChild(txtElem); /* place text elements under <g> tag */
              }
            }
          }else{
            var txtElem = makeTxtElement(tmpParam)
            txtElem.append(param.title);
            gElem.appendChild(txtElem); /* place text elements under <g> tag */
          }

          // 如果 badge 大於 1 時，呈現 badge ( 要加判斷式 ) ----------------------
          if(param.badge && param.badge > 1 && param.action != 'ex'){
            tstyle_str='stroke:none;fill:yellow;font-size:16';

            var txtElemBadge = makeTxtElement({ svgns: svgns, cx: param.x+10, cy: param.y+(StatusHeight-9),
                                        txt_anchor: "start", style_str: tstyle_str,
                                        onclick: onclick_str})
            txtElemBadge.append(param.badge);
            gElem.appendChild(txtElemBadge);

            v_svg.appendChild(gElem);
          }
      }

      function getFontSize(data){
        var maxLen = 0;
        var output = {maxLen: 0, fontSize: 16};

        for(var i = 0; i<data.length; i++){
          var tubeName = data[i].tubeName;
          maxLen = Math.max(maxLen, tubeName.length);
        }

        output.maxLen = maxLen;

        if(maxLen <= 6){
          output.fontSize = 18
        }else if(maxLen <= 16){
          output.fontSize = 14;
        }else{
          output.fontSize = 10;
        }

        return output;
      }

      // ===============================================================================
      /*
        x:
        y:
        height:
        style:
        rx:
        ry:
        width:
        id:
        onclick:
        start_time:
        end_time:
      */
      function makeRectElement(param){
        var rectElem  = document.createElementNS(svgns, "rect");
        rectElem.setAttributeNS(null,"x",param.x);
        rectElem.setAttributeNS(null,"y",param.y);
        rectElem.setAttributeNS(null,"height",param.height);
        rectElem.setAttributeNS(null,"width",(param.width < 0)? 0:param.width);

        if(param.id){
          rectElem.setAttributeNS(null,"id",param.id);
        }
        if(param.rx){
          rectElem.setAttributeNS(null,"rx",param.rx);
        }
        if(param.ry){
          rectElem.setAttributeNS(null,"ry",param.ry);
        }
        if(param.style){
          rectElem.setAttributeNS(null,"style",param.style);
        }
        if(param.onclick){
          rectElem.setAttributeNS(null,"onclick",param.onclick);
        }
        return rectElem;
      }

      /*
        svgns:
        cx:
        cy:
        txt_anchor:
        style_str:
        id:
        onclick:
        fontSize:
      */
       function makeTxtElement(param){
        var txtElem=document.createElementNS(svgns, "text");
        txtElem.setAttributeNS(null,"x",param.cx);
        txtElem.setAttributeNS(null,"y",param.cy);
        txtElem.setAttributeNS(null,"dy",".35em");
        txtElem.setAttributeNS(null,"text-anchor",param.txt_anchor);
        txtElem.setAttributeNS(null,"style",param.style_str);
        if(param.id){
          txtElem.setAttributeNS(null,"id",param.id);
        }
        if(param.onclick){
          txtElem.setAttributeNS(null,"onclick",param.onclick);
        }
        if(param.fontSize){
          txtElem.setAttributeNS(null,"font-size",param.fontSize);
        }
        return txtElem;
      }

      var displaySVG = function(data, svg) {
          opStatus = data;
          setupSVG(svg)
      }



    }//END link: function (scope, element, attrs) {
  }//END return {
}]);//END app.directive('svgInOp', ['$window','$compile', function ($window,$compile) {



