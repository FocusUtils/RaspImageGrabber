function prevent_submit_and_unfocus(e) {
    document.activeElement.blur()
    e.preventDefault();
}

function isNumeric(str) {
    if (typeof str != "string") return false; // we only process strings!
    return (
        (!isNaN(str) && // use type coercion to parse the _entirety_ of the string (`parseFloat` alone does not do this)...
            !isNaN(parseFloat(str))) || // ...and ensure strings of whitespace fail
        str === ""
    ); // except completly empty to ease the retyping of the first digit
}

let img_aspect_ratio;
let img;
let dpr_value;
let mspr_value;
let lowercase_steps = 1;
let uppercase_steps = 1;


function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}
  

function adjust_image_size() {
    const img_container = $("#image-container");
    const btn_container = $(".button-container")[0];
    const img_container_aspect_ratio = img_container.width() / img_container.height();

    let new_width;
    let new_height;

    $.get("/settings/with-bms-cam", (async = false), (value) => {
        if (value === "False") {
            console.log("not bms cam");
            $(img_container).css("height", "4em");
            $(btn_container).css("height", "80%");
        }
    });
    

    if (img_container_aspect_ratio > img_aspect_ratio) {
        new_height = img_container.height();
        new_width = new_height * img_aspect_ratio;
    } else {
        new_width = img_container.width();
        new_height = new_width / img_aspect_ratio;
    }
    
    img.width(new_width);
    img.height(new_height);
}

class HoldableButton {
    constructor(button, callback) {
        this.button = button;
        this.pressed = false;
        this.pressed_since = 0;
        this.callback = callback;

        $(this.button).on("pointerdown", () => {
            this.pressed = true;
            this.pressed_since = Date.now();
            this.callback("press");
        })

        $(this.button).on("pointerup", () => {
            this.pressed = false;
        })
        
        $(this.button).on("mouseleave", () => {
            this.pressed = false;
        })

        $(this.button).on("touchend", () => {
            this.pressed = false;
        })

        setTimeout(this.worker, 0, this);
    }

    async worker(obj) {
        while (true) {
            if (obj.pressed_since + 500 < Date.now() && obj.pressed) {
                obj.callback("hold");
                await delay(50);
            } else {
                await delay(20);
            }
        }
    }
}

function update_curr_pos() {
    $.ajax({
        url: "/microscope/current",
        type: "GET",
        success: function (data) {
            $("#pos-in-steps-input").val(data);
            let distance_per_step = dpr_value / mspr_value;
            let total_distance = data * distance_per_step;

            $("#pos-in-unit-input").val(total_distance);
        }
    });
}

function update_start_pos() {
    $.ajax({
        url: "/microscope/start",
        type: "GET",
        success: function (data) {
            let distance_per_step = dpr_value / mspr_value;
            let total_distance = data * distance_per_step;
            $("#start-in-unit-input").val(total_distance);
        }
    });
}

function update_end_pos() {
    $.ajax({
        url: "/microscope/end",
        type: "GET",
        success: function (data) {
            let distance_per_step = dpr_value / mspr_value;
            let total_distance = data * distance_per_step;
            $("#end-in-unit-input").val(total_distance);
        }
    });
}

$(window).on("load", () => {
    $.get("/settings/motor-rotation-units", (async = false), (value) => {
        const distances = {1:"m", 3:"mm", 6:"µm", 9: "nm", 12: "pm"}
        $(".unit").html(distances[value]);
    });
    $.get("/settings/lowercase-motor-steps", (async = false), (value) => {
        lowercase_steps = parseInt(value);
    });

    $.get("/settings/uppercase-motor-steps", (async = false), (value) => {
        uppercase_steps = parseInt(value);
    });
    
    $.get("/settings/steps-per-motor-rotation", (async = false), (value) => {
        mspr_value = parseFloat(value);
    });

    $.get("/settings/distance-per-motor-rotation", (async = false), (value) => {
        dpr_value = parseFloat(value);
    });

    img = $("#live-image");
    img_aspect_ratio = img.width() / img.height();
    adjust_image_size();

    const pos_in_steps_input = document.getElementById("pos-in-steps-input"); 
    let pos_in_steps_value = pos_in_steps_input.value;
    
    const pos_in_unit_input = document.getElementById("pos-in-unit-input"); 
    let pos_in_unit_value = pos_in_unit_input.value;

    const start_input = document.getElementById("start-in-unit-input"); 
    let start_value = start_input.value;
    
    const end_input = document.getElementById("end-in-unit-input"); 
    let end_value = end_input.value;
    
    $("form").submit(prevent_submit_and_unfocus);

    // button events

    new HoldableButton($("#move-up"), function (prs_hld) {
        $.get(`/microscope/move-by/${lowercase_steps}`, (async = false));
        update_curr_pos();
    });

    new HoldableButton($("#move-down"), function (prs_hld) {
        $.get(`/microscope/move-by/-${lowercase_steps}`, (async = false));
        update_curr_pos();
    })

    new HoldableButton($("#move-up-2"), function (prs_hld) {
        $.get(`/microscope/move-by/${uppercase_steps}`, (async = false));
        update_curr_pos();
    });

    new HoldableButton($("#move-down-2"), function (prs_hld) {
        $.get(`/microscope/move-by/-${uppercase_steps}`, (async = false));
        update_curr_pos();
    })
 
    // manual button updates

    $("#set-start").on("pointerdown", () => {
        $.post("/microscope/start", (async = false));
        update_start_pos();
    });

    $("#set-ending").on("pointerdown", () => {
        $.post("/microscope/end", (async = false));
        update_end_pos();
    });

    $("#move-start").on("pointerdown", () => {
        $.get("/microscope/move/start", (async = false));
        update_curr_pos();
    });

    $("#move-ending").on("pointerdown", () => {
        $.get("/microscope/move/end", (async = false));
        update_curr_pos();
    });

    $("#pos-in-steps-input").on("focusout", () => {
        $.get(`/microscope/move-to/${pos_in_steps_input.value}`, (async = false));
        update_curr_pos();
    })

    $("#pos-in-unit-input").on("focusout", () => {
        $.get(`/microscope/move-to/${pos_in_steps_input.value}`, (async = false));
        update_curr_pos();
    })

    $(pos_in_steps_input).on("keyup", function (e) {
        if (isNumeric(pos_in_steps_input.value) === false) {
            pos_in_steps_input.value = pos_in_steps_value;
        } else {
            if (pos_in_steps_input.value === "") {
            } else {
                pos_in_steps_value = parseFloat(pos_in_steps_input.value);
                let distance_per_step = dpr_value / mspr_value;
                let total_distance = pos_in_steps_value * distance_per_step;
    
                $("#pos-in-unit-input").val(total_distance);
            }
        }
    });

    $(pos_in_unit_input).on("keyup", function (e) {
        if (isNumeric(pos_in_unit_input.value) === false) {
            pos_in_unit_input.value = pos_in_unit_value;
        } else {
            if (pos_in_unit_input.value === "") {
            } else {
                pos_in_unit_value = parseFloat(pos_in_unit_input.value);
                let distance_per_step = dpr_value / mspr_value;
                pos_in_steps_value = pos_in_unit_value / distance_per_step;
                pos_in_steps_input.value = pos_in_steps_value;
            }
        }
    });

    $(start_input).on("keyup", function (e) {
        if (isNumeric(start_input.value) === false) {
            start_input.value = start_value;
        } else {
            if (start_input.value === "") {
            } else {
                start_value = parseFloat(start_input.value);
                let distance_per_step = dpr_value / mspr_value;
                let total_distance = start_value / distance_per_step;
                $.post(`/microscope/start/${total_distance}`, (async = false));
            }
        }
    });

    $(end_input).on("keyup", function (e) {
        if (isNumeric(end_input.value) === false) {
            end_input.value = end_value;
        } else {
            if (end_input.value === "") {
            } else {
                end_value = parseFloat(end_input.value);
                let distance_per_step = dpr_value / mspr_value;
                let total_distance = end_value / distance_per_step;
                $.post(`/microscope/end/${total_distance}`, (async = false));
            }
        }
    });

    $("#continue-to-stepsetter").on("pointerdown", () => {
        $.ajax({
            url: "/microscope/end",
            type: "GET",
            success: function (ending) {
                $.ajax({
                    url: "/microscope/start",
                    type: "GET",
                    success: function (start) {
                        location.href = `stepsetter`;
                    }
                });
            }
        });
    });

    setTimeout(() => {
        update_curr_pos();
        update_start_pos();
        update_end_pos();
    }, 50)
});

addEventListener("resize", adjust_image_size);
