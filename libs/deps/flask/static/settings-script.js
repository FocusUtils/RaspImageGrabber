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

$(window).on("load", () => {
    const mspr_input = document.getElementById("motor-steps-per-rotation-input");
    const dpr_input = document.getElementById("distance-per-rotation-input");
    const digi_cam_delay_input = document.getElementById("digi-cam-delay-input")
    const shake_rest_delay_input = document.getElementById("shake-rest-delay-input")
    const lowercase_motor_steps_input = document.getElementById("lowercase-motor-steps-input")
    const uppercase_motor_steps_input = document.getElementById("uppercase-motor-steps-input")
    const sleep_time_after_step_input = document.getElementById("sleep-time-after-step-input")
    const whatsapp_number_input = document.getElementById("whatsapp-number-input");
    const whatsapp_api_key_input = document.getElementById("whatsapp-api-key-input")
    const execution_mode_input = document.getElementById("execution-mode-input")

    let mspr_value = mspr_input.value;
    let dpr_value = dpr_input.value;
    let digi_cam_delay_value = digi_cam_delay_input.value;
    let shake_rest_delay_value = shake_rest_delay_input.value;
    let lowercase_motor_steps_value = lowercase_motor_steps_input.value;
    let uppercase_motor_steps_value = uppercase_motor_steps_input.value;
    let sleep_time_after_step_value = sleep_time_after_step_input.value;
    let whatsapp_number_value = whatsapp_number_input.value;
    let whatsapp_api_key_value = whatsapp_api_key_input.value;
    let execution_mode_value = execution_mode_input.value;

    // event handlers

    $("form").submit(prevent_submit_and_unfocus);
    
    $(".submit-button").on("click", function () {
        const attr_id =  $(this).attr("for")
        
        const id_name_table = {
            "gpio-default-on-input": "GPIO-default-on",
            "gpio-motor-pins-input": "GPIO-motor-pins",
            "gpio-camera-pin-input": "GPIO-camera-pin",
            "execution-mode-input": "execution-mode"
        }

        const attr_name = id_name_table[attr_id];

        let value = $(`#${attr_id}`).val();
        if (attr_id === "gpio-motor-pins-input") {
            value = `[${value}]`
        }

        $.post(`/settings/${attr_name}/${value}`);
    })

    $("#units-input").on("change", function () {
        
        $.post(`/settings/motor-rotation-units/${Math.log10(this.value)}`);
        $(".unit").html($("#units-input option:selected").text());
    });

    
    $(mspr_input).on("keyup", function (e) {
        if (isNumeric(mspr_input.value) === false) {
            mspr_input.value = mspr_value;
        } else {
            if (mspr_input.value === "") {
            } else {
                mspr_value = parseFloat(mspr_input.value);
                $.post(`/settings/steps-per-motor-rotation/${mspr_input.value}`);
            }
        }

    });

    $(dpr_input).on("keyup", function (e) {
        if (isNumeric(dpr_input.value) === false) {
            dpr_input.value = dpr_value;
        } else {
            if (dpr_input.value === "") {
            } else {
                dpr_value = parseFloat(dpr_input.value);
                $.post(`/settings/distance-per-motor-rotation/${dpr_input.value}`);
            }
        }

    });

    $(digi_cam_delay_input).on("keyup", function (e) {
        if (isNumeric(digi_cam_delay_input.value) === false) {
            digi_cam_delay_input.value = digi_cam_delay_value;
        } else {
            if (digi_cam_delay_input.value === "") {
            } else {
                digi_cam_delay_value = parseFloat(digi_cam_delay_input.value);
                $.post(`/settings/digi-cam-delay/${digi_cam_delay_input.value}`);
            }
        }

    });

    $(shake_rest_delay_input).on("keyup", function (e) {
        if (isNumeric(shake_rest_delay_input.value) === false) {
            shake_rest_delay_input.value = shake_rest_delay_value;
        } else {
            if (shake_rest_delay_input.value === "") {
            } else {
                shake_rest_delay_value = parseFloat(shake_rest_delay_input.value);
                $.post(`/settings/shake-rest-delay/${shake_rest_delay_input.value}`);
            }
        }

    });

    $(lowercase_motor_steps_input).on("keyup", function (e) {
        if (isNumeric(lowercase_motor_steps_input.value) === false) {
            lowercase_motor_steps_input.value = lowercase_motor_steps_value;
        } else {
            if (lowercase_motor_steps_input.value === "") {
            } else {
                lowercase_motor_steps_value = parseFloat(lowercase_motor_steps_input.value);
                $.post(`/settings/lowercase-motor-steps/${lowercase_motor_steps_input.value}`);
            }
        }

    });

    $(uppercase_motor_steps_input).on("keyup", function (e) {
        if (isNumeric(uppercase_motor_steps_input.value) === false) {
            uppercase_motor_steps_input.value = uppercase_motor_steps_value;
        } else {
            if (uppercase_motor_steps_input.value === "") {
            } else {
                uppercase_motor_steps_value = parseFloat(uppercase_motor_steps_input.value);
                $.post(`/settings/uppercase-motor-steps/${uppercase_motor_steps_input.value}`);
            }
        }
    });

    $(sleep_time_after_step_input).on("keyup", function (e) {
        if (isNumeric(sleep_time_after_step_input.value) === false) {
            sleep_time_after_step_input.value = sleep_time_after_step_value;
        } else {
            if (sleep_time_after_step_input.value === "") {
            } else {
                sleep_time_after_step_value = parseFloat(sleep_time_after_step_input.value);
                $.post(`/settings/sleep-time-after-step/${sleep_time_after_step_input.value}`);
            }
        }
    });

    $(whatsapp_number_input).on("keyup", function (e) {
        if (isNumeric(whatsapp_number_input.value) === false) {
            whatsapp_number_input.value = whatsapp_number_value;
        } else {
            if (whatsapp_number_input.value === "") {
            } else {
                whatsapp_number_value = parseFloat(whatsapp_number_input.value);
                $.post(`/settings/whatsapp-number/${whatsapp_number_input.value}`);
            }
        }
    });

    $(whatsapp_number_input).on("keyup", function (e) {
        if (isNumeric(whatsapp_number_input.value) === false) {
            whatsapp_number_input.value = whatsapp_number_value;
        } else {
            if (whatsapp_number_input.value === "") {
            } else {
                whatsapp_number_value = parseFloat(whatsapp_number_input.value);
                $.post(`/settings/whatsapp-number/${whatsapp_number_input.value}`);
            }
        }
    });

    $(whatsapp_api_key_input).on("keyup", function (e) {
        if (isNumeric(whatsapp_api_key_input.value) === false) {
            whatsapp_api_key_input.value = whatsapp_api_key_value;
        } else {
            if (whatsapp_api_key_input.value === "") {
            } else {
                whatsapp_api_key_value = parseFloat(whatsapp_api_key_input.value);
                $.post(`/settings/whatsapp-api-key/${whatsapp_api_key_input.value}`);
            }
        }
    });

    // load saved values

    $.get("/settings/GPIO-default-on", (async=false), (value) => {
        $("#gpio-default-on-input").val(value);
    });

    $.get("/settings/GPIO-motor-pins", (async=false), (value) => {
        $("#gpio-motor-pins-input").val(value.substring(1, value.length-1));
    });

    $.get("/settings/GPIO-camera-pin", (async=false), (value) => {
        $("#gpio-camera-pin-input").val(parseInt(value))
    });

    $.get("/settings/motor-rotation-units", (async = false), (value) => {
        $("#units-input").val(Math.pow(10, parseInt(value)), value)
        $(".unit").html($("#units-input option:selected").text());
    });

    $.get("/settings/steps-per-motor-rotation", (async = false), (value) => {
        $("#motor-steps-per-rotation-input").val(parseFloat(value))
    });

    $.get("/settings/distance-per-motor-rotation", (async = false), (value) => {
        $("#distance-per-rotation-input").val(parseFloat(value))
    });

    $.get("/settings/digi-cam-delay", (async = false), (value) => {
        $("#digi-cam-delay-input").val(parseFloat(value))
    });

    $.get("/settings/shake-rest-delay", (async = false), (value) => {
        $("#shake-rest-delay-input").val(parseFloat(value))
    });

    $.get("/settings/lowercase-motor-steps", (async = false), (value) => {
        $("#lowercase-motor-steps-input").val(parseInt(value))
    });

    $.get("/settings/uppercase-motor-steps", (async = false), (value) => {
        $("#uppercase-motor-steps-input").val(parseInt(value))
    });

    $.get("/settings/sleep-time-after-step", (async = false), (value) => {
        $("#sleep-time-after-step-input").val(parseFloat(value))
    });

    $.get("/settings/whatsapp-number", (async = false), (value) => {
        $("#whatsapp-number-input").val(parseFloat(value))
    });

    $.get("/settings/whatsapp-api-key", (async = false), (value) => {
        $("#whatsapp-api-key-input").val(parseFloat(value))
    });
    $.get("/settings/execution-mode", (async = false), (value) => {
        $("#execution-mode-input").val(value);
    });
});
