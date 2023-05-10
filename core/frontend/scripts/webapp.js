(function() {
    function wl_item_btn_flip_flip(event) {
        var wl_item_card = event.target.closest(".wl-item-card");
        if (wl_item_card) {
            wl_item_card.classList.toggle("flipped");
        }
    }

    function wl_fav_swtch_notify_submit(event) {
        var wl_fav_form_notify = event.target.form;
        wl_fav_form_notify.submit();
    }

    document.addEventListener('DOMContentLoaded', function() {
        if (document.body.dataset.viewname == "wishlist") {
            for (var wl_item_btn_flip of document.querySelectorAll('.wl-item-btn-flip')) {
                wl_item_btn_flip.addEventListener('click', wl_item_btn_flip_flip, false);
            }
        }
        if (document.body.dataset.viewname == "start" || document.body.dataset.viewname == "favorites") {
            for (var wl_fav_swtch_notify of document.querySelectorAll('.wl-fav-swtch-notify')) {
                wl_fav_swtch_notify.addEventListener('change', wl_fav_swtch_notify_submit, false);
            }
        }
        document.querySelectorAll('button[type="submit"]').forEach(submit_btn => {
            submit_btn.addEventListener('click', function(event) {
                setTimeout(function () {
                    status_element = submit_btn.querySelector('[role="status"]')
                    if (status_element) {
                        status_element.classList.remove("d-none");
                    }
                    event.target.disabled = true;
                }, 0);
            });
        });
    });

})();
