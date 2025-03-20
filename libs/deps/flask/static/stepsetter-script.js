function isNumeric(str) {
    if (typeof str != "string") return false; // we only process strings!
    return (
        (!isNaN(str) && // use type coercion to parse the _entirety_ of the string (`parseFloat` alone does not do this)...
            !isNaN(parseFloat(str))) || // ...and ensure strings of whitespace fail
        str === ""
    ); // except completly empty to ease the retyping of the first digit
}

function prevent_submit_and_unfocus(e) {
    document.activeElement.blur()
    e.preventDefault();
}

const getUrIParameter = function getUrlParameter(sParam) {
    let sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
    return false;
};

$(window).on("load", () => {
    // load saved values
    var total_steps;
    let dpr_value;
    let mspr_value;
    const idd_input = document.getElementById("image-delta-distance-input");
    const tia_input = document.getElementById("total-image-amount-input");

    $.get("/settings/microscope-start", (async = false), (start_pos) => {
        $.get("/settings/microscope-end", (async = false), (end_pos) => {
            total_steps = Math.abs(parseInt(start_pos) - parseInt(end_pos));
            $("#total-steps").text(total_steps)
            update_all(false);
        });
    });

    $.get("/settings/motor-rotation-units", (async = false), (value) => {
        const distances = {1:"m", 3:"mm", 6:"µm", 9: "nm", 12: "pm"}
        $(".unit").html(distances[value]);
    });

    $.get("/settings/steps-per-motor-rotation", (async = false), (value) => {
        mspr_value = parseFloat(value);
        update_all(false);
    });

    $.get("/settings/distance-per-motor-rotation", (async = false), (value) => {
        dpr_value = parseFloat(value);
        update_all(false);
    });

    $.get("/settings/image-count", (async = false), (value) => {
        console.log(value);
        tia_input.value = value;
        tia_value = parseFloat(value);
        update_all(false);
    });

    let progressBar = document.getElementById("recording-progress-beam");
    let progressNum = document.getElementById("progress-value-num")
    progressBar.style.width = "0%";

    $.get(`/recording-progress`).done((data) => {
        
        const processed_data = $.parseJSON(data);
        progressBar.style.width = `${processed_data[0]}%`;
        progressNum.innerHTML = `${processed_data[1]}`
    });

    const socket = new WebSocket(`ws://${window.location.hostname}:65432`);

    socket.addEventListener("open", () => {
        // send a message to the server
        socket.send(null)
        console.log("connected")
    });

    // receive a message from the server
    socket.addEventListener("message", ({ data }) => {
        const processed_data = $.parseJSON(data);
        progressBar.style.width = `${processed_data[0]}%`;
        progressNum.innerHTML = `${processed_data[1]}`
        socket.send(data);
    });


    $("#image-delta-distance-form").submit(prevent_submit_and_unfocus);
    $("#total-image-amount-form").submit(prevent_submit_and_unfocus);

    let idd_value = idd_input.value;
    let tia_value = tia_input.value;

    let latest_typed = tia_input;

    function update_all(update_server_values = true) {
        let distance_per_step = dpr_value / mspr_value;
        let total_distance = total_steps * distance_per_step;

        if (latest_typed === idd_input) {
            tia_value = total_distance / idd_value;
            tia_input.value = tia_value;
        }

        if (latest_typed === tia_input) {

            idd_value = total_distance / tia_value;
            idd_input.value = idd_value;
        }

        if (tia_value != Infinity && idd_value != Infinity && update_server_values) {
            $.get(`/settings/recording`).done((data) => {
                if (data === "False") {
                    console.log("updating values");
                    $.post(`/image-count/${tia_value}`);
                }
            });
        }

    }

    $(idd_input).on("keyup", function (e) {
        if (isNumeric(idd_input.value) === false) {
            idd_input.value = idd_value;
        } else {
            if (idd_input.value === "") {
            } else {
                idd_value = parseFloat(idd_input.value);
            }
        }

        latest_typed = idd_input;
        update_all()
    });

    $(tia_input).on("keyup", function (e) {
        if (isNumeric(tia_input.value) === false) {
            tia_input.value = tia_value;
        } else {
            if (tia_input.value === "") {
            } else {
                tia_value = parseFloat(tia_input.value);
            }
        }

        latest_typed = tia_input;
        update_all()
    });

    $("#record-images").on("pointerdown", () => {
        $.get("/record-images", (async = false), () => {
            $("#record-images").html("Started recording!")
        });
    });
});
