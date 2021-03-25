$(document).ready(function() {
  var storPeers = $.jStorage.get("peers", {});
  var panels = $.jStorage.get("panels", {});
  if (typeof panels["default"] === "undefined") {
    panels["default"] = {title: "Все звонки",
                         color: "success",
                         size: 12};
  }

  var dialog = $(".dialog-config");
  var sort_div = $("#sortable");

  //Building panels
  var call_containers = {};
  var panel_index = 1;
  var container_body = sort_div;
  new_container("default", panels["default"]);
  $.each(panels, function(k, v) {
    if (!isNaN(k)) {
      new_container(k, v);
    }
  });
  sort_div.sortable({
    handle: ".panel-heading",
    cursor: "move",
    start: function(event, ui) {
      if (!dialog.hasClass("hide")) {
        dialog.find(".config-close").click();
      }
    },
    update: function(event, ui) {
      $.jStorage.set("panel_pos", $(this).sortable("toArray"));
    }
  });
  $(".panel-heading").disableSelection();
  resort_containers();

  //Panel icon actions
  $(".panel-signs > .glyphicon").on("click", function(e) {
    var panel = $(this).closest(".panel");
    var panel_id = panel.find(".container-calls").data("id");
    if ($(this).hasClass("action-collapse")) {
      dialog.addClass("hide");
      panel.find(".panel-body").toggleClass("hide").end()
        .find(".action-config").removeClass("action-config-clicked");
      $(this).toggleClass("glyphicon-chevron-down glyphicon-chevron-right");
    }
    else if ($(this).hasClass("action-add")) {
      if (!dialog.hasClass("hide")) {
        dialog.find(".config-close").click();
      }
      dialog.css({
        right: $(window).width() / 2 - 118,
        top: $(window).height() / 2 - 150
      }).find(".config-color").attr("class", "").addClass("form-control config-color config-color-primary").val("primary").end()
        .find(".config-size").val("12").end()
        .find(".config-add").removeClass("hide").end()
        .removeClass("hide").data("id", "new")
        .find(".config-title").val("").focus();
    }
    else if ($(this).hasClass("action-config")) {
      if (panel.find(".action-collapse").hasClass("glyphicon-chevron-down")) {
        if (!dialog.hasClass("hide")) {
          dialog.find(".config-close").click();
        }
        dialog.css({
            right: $(window).width() - (panel.offset().left + panel.width() - 5),
            top: $(this).offset().top + $(this).height() + 5
          }).find(".config-color").attr("class", "").addClass("form-control config-color config-color-" + panels[panel_id].color).val(panels[panel_id].color).end()
          .find(".config-size").val(panels[panel_id].size).end()
          .find(".config-add").addClass("hide").end()
          .removeClass("hide").data("id", panel_id)
          .find(".config-title").val(panels[panel_id].title).focus();
        $(this).addClass("action-config-clicked");

      }
    }
    else if ($(this).hasClass("action-remove")) {
      if (panel_id !== "default") {
        if (!dialog.hasClass("hide")) {
          dialog.find(".config-close").click();
        }
        if (confirm("Вы действительно хотите удалить группу: " + panels[panel_id].title + "?")) {
          delete panels[panel_id];
          $.jStorage.set("panels", panels);
          call_containers["default"].trigger("ss-destroy")
            .append(call_containers[panel_id].trigger("ss-destroy").find(".call").attr("style", "").end().html())
            .shapeshift(shapeshift_config).trigger("ss-rearranged");
          delete call_containers[panel_id];
          panel.parent().remove();
        }
      }
    }
  });

  //Moving dialog window if browser resized
  $(window).resize(function() {
    if (!dialog.hasClass("hide")) {
      var panel_id = dialog.data("id");
      if (panel_id === "new") {
        dialog.css({
          right: $(window).width() / 2 - 118,
          top: $(window).height() / 2 - 150
        });
      }
      else {
        var panel = call_containers[panel_id].closest(".panel");
        var btn = panel.find(".action-config");
        dialog.css({
          right: $(window).width() - (panel.offset().left + panel.width() - 5),
          top: btn.offset().top + btn.height() + 5
        })
      }
    }
  });

  //Dialog actions
  $(".config-color").on("change", function() {
    $(this).attr("class", "").addClass("form-control config-color config-color-" + $(this).val());
  });

  $("#config").on("submit", function() {
    var panel_id = dialog.data("id");
    var panel_param = {title: $(this).find(".config-title").val(),
                       color: $(this).find(".config-color").val(),
                       size: parseInt($(this).find(".config-size").val(), 10)};
    if (panel_param.size < 2) panel_param.size = 2;
    if (panel_param.size > 12) panel_param.size = 12;
    if (panel_id === "new") {
      panel_id = panel_index;
      new_container(panel_id, panel_param);
      call_containers[panel_id].shapeshift(shapeshift_config);
      $.jStorage.set("panel_pos", sort_div.sortable("toArray"));
    }
    else {
      call_containers[panel_id].closest(".panel").removeClass("panel-" + panels[panel_id].color).addClass("panel-" + panel_param.color)
        .find(".panel-txt").text(panel_param.title).end()
        .find(".action-config").removeClass("action-config-clicked").end()
        .parent().removeClass("col-lg-" + panels[panel_id].size).addClass("col-lg-" + panel_param.size).end().end()
        .trigger("ss-rearrange");
    }
    dialog.addClass("hide");
    panels[panel_id] = panel_param;
    $.jStorage.set("panels", panels);
    return false;
  });

  $("#config .config-close").on("click", function() {
    dialog.addClass("hide");
    if (dialog.data("id") !== "new") {
      call_containers[dialog.data("id")].closest(".panel").find(".action-config").removeClass("action-config-clicked");
    }
  });

  $(document).on("keyup", function(e) {
    if (e.keyCode == 27 && !dialog.hasClass("hide")) {
      dialog.find(".config-close").click();
    }
  });

  //WebSocket Calls
  var socket = new WebSocket("ws://" + ws_ip + ":" + ws_port);
  socket.onmessage = function(event) {
    var id = "";
    var peer = "";
    var data = $.parseJSON(event.data);
    switch (data.action) {
      case "setid": //Setting IDs
        id = data.id;
        socket.send(JSON.stringify({
          action: "start",
          id: id
        }));
        break;
      case "peers": //Loading peers
        $.each(data.peers, function(k, v) {
          if (!isNaN(v.number)) {
            if (typeof storPeers[v.number] === "undefined") {
              storPeers[v.number] = {container: "default",
                                     index: 0};
            }
            call_containers[storPeers[v.number]["container"]]
              .append('<div class="call" data-id="' + v.number + '" id="num_' + v.number + '">' + v.name + ' (' + v.number + ')</div>');
            $("#num_" + v.number).data("index", storPeers[v.number]["index"]);
            if (v.status == "free") $("#num_" + v.number).addClass("online");
            else if (v.status == "busy") $("#num_" + v.number).addClass("busy");
          }
        });
        init_containers($(".container-fluid .container-calls"), "index");
        break;
      case "status": //Setting statuses
        peer = $("#num_" + data.peer);
        if (["Registered", "Reachable"].includes(data.status) && !peer.hasClass("busy")) {
          peer.addClass("online");
        }
        else if (["Unregistered", "Unreachable"].includes(data.status)) {
          peer.removeClass("online");
        }
        break;
      case "peerstatus": //Setting peer call status
        peer = $("#num_" + data.peer);
        if (data.status == "busy") {
          peer.removeClass("online").addClass("busy");
        }
        else if (data.status == "free") {
          peer.removeClass("busy").addClass("online");
        }
        break;
    }
  };

  //Initialize containers
  function init_containers(containers, id) {
    $.each(containers, function() {
      $(this).find("div").sort(function(a, b) {
        return parseInt($(a).data(id)) - parseInt($(b).data(id));
      }).appendTo($(this));
    });
    containers.shapeshift(shapeshift_config);
    $.jStorage.set("peers", storPeers);
  }

  //Adding new container
  function new_container(index, value) {
    var etalon = $(".etalon").children().clone(true, true);
    etalon.addClass("col-lg-" + value.size).attr("id", "container_" + index)
      .find(".panel").addClass("panel-" + value.color).end()
      .find(".panel-txt").text(value.title).end()
      .find(".action-remove").removeClass("hide").end()
      .find(".container-calls").attr("data-id", index);
    if (index === "default") {
      etalon.find(".action-remove").remove();
    }
    else {
      var idx = parseInt(index, 10);
      if (panel_index <= idx) {
        panel_index = idx + 1;
      }
    }
    etalon.appendTo(container_body);
    call_containers[index] = container_body.find(".container-calls").filterByData("id", index);
    //rearranged
    call_containers[index].on("ss-rearranged ss-removed ss-added", function() {
      update_containers($(this));
    });
  }

  //Update container
  function update_containers (container) {
    var container_id = container.data("id");
    var objects = container.children();
    objects.each(function() {
      storPeers[$(this).data("id")] = {index: $(this).index(),
                                       container: container_id};
    });
    $.jStorage.set("peers", storPeers);
  }

  //Resorting containers
  function resort_containers() {
    var panel_sort = $.jStorage.get("panel_pos", []);
    if (!panel_sort.length) {
      $.jStorage.set("panel_pos", sort_div.sortable("toArray"));
      return;
    }
    for (var i = 0; i < panel_sort.length; i++) {
      $("#" + panel_sort[i]).appendTo(sort_div);
    }
  }

  //Working with load/save/reset configs
  $("#import_config :file").fileReaderJS({
    accept: false,
    readAsMap: {
      "application/json": "Text"
    },
    readAsDefault: 'Text',
    on: {
      load: function (e, file) {
        var json_file = true;
        try {
          load_data = $.parseJSON(e.target.result);
        }
        catch(err) {
          json_file = false;
        }
        if (json_file && "application" in load_data && load_data["application"] === "Asterisk Call Activity Monitor Config") {
          if (confirm("Вы действительно хотите загрузить эти настройки?")) {
            if ("panels" in load_data) $.jStorage.set("panels", load_data["panels"]);
            if ("peers" in load_data) $.jStorage.set("peers", load_data["peers"]);
            if ("panel_pos" in load_data) $.jStorage.set("panel_pos", load_data["panel_pos"]);
          }
        }
        else {
          alert("Неверный формат файла");
        }
        $(location).attr("href", ".");
      }
    }
  });

  $("#export_config").on("click", function() {
    var save_data = {
      application: "Asterisk Call Activity Monitor Config",
      panels: $.jStorage.get("panels", {}),
      peers: $.jStorage.get("peers", {}),
      panel_pos:  $.jStorage.get("panel_pos", [])

    };
    var blob = new Blob([JSON.stringify(save_data)], {type: "application/json;charset=utf-8"});
    saveAs(blob, "calls.json");
  });

  $("#reset_config").on("click", function() {
    if (confirm("Вы действительно хотите сбросить настройки?")) {
      $.jStorage.deleteKey("panels");
      $.jStorage.deleteKey("peers");
      $.jStorage.deleteKey("panels");
      $(location).attr("href", ".");
    }
  });
});