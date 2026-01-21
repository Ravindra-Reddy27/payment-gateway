import './styles.css';

class PaymentGateway {
    constructor(options) {
        // [cite: 459-468] Options: key, orderId, callbacks
        if (!options.key || !options.orderId) {
            console.error("PaymentGateway: 'key' and 'orderId' are required.");
            return;
        }

        this.key = options.key;
        this.orderId = options.orderId;
        this.onSuccess = options.onSuccess || (() => {});
        this.onFailure = options.onFailure || (() => {});
        this.onCloseCallback = options.onClose || (() => {});

        this.handleMessage = this.handleMessage.bind(this);
    }

 open() {
        // 1. Create the Main Wrapper (The Root)
        // [cite: 510] <div id="payment-gateway-modal" data-test-id="payment-modal">
        this.modalRoot = document.createElement('div');
        this.modalRoot.id = 'payment-gateway-modal';
        this.modalRoot.setAttribute('data-test-id', 'payment-modal');

        // 2. Create the Overlay
        // [cite: 511] <div class="modal-overlay">
        this.overlay = document.createElement('div');
        this.overlay.className = 'modal-overlay';

        // 3. Create the Content Container
        // [cite: 512] <div class="modal-content">
        this.content = document.createElement('div');
        this.content.className = 'modal-content';

        // 4. Create the Close Button
        // [cite: 517-521] <button data-test-id="close-modal-button" class="close-button">
        this.closeBtn = document.createElement('button');
        this.closeBtn.className = 'close-button';
        this.closeBtn.setAttribute('data-test-id', 'close-modal-button');
        this.closeBtn.innerHTML = '&times;';
        this.closeBtn.onclick = () => this.close();

        // 5. Create the Iframe
        // [cite: 513-516] <iframe data-test-id="payment-iframe" ...>
        this.iframe = document.createElement('iframe');
        this.iframe.setAttribute('data-test-id', 'payment-iframe');
        // We add '&embedded=true' to match the example query params
        this.iframe.src = `http://localhost:5173/checkout?order_id=${this.orderId}&embedded=true`; 
        
        // 6. Assemble the Nesting
        // Iframe and Button go inside Content
        this.content.appendChild(this.iframe);
        this.content.appendChild(this.closeBtn);
        
        // Content goes inside Overlay
        this.overlay.appendChild(this.content);
        
        // Overlay goes inside Root
        this.modalRoot.appendChild(this.overlay);

        // Root goes attached to Body
        document.body.appendChild(this.modalRoot);

        // 7. Listener
        window.addEventListener('message', this.handleMessage);
    }

    close() {
        if (this.modalRoot) {
            document.body.removeChild(this.modalRoot);
            this.modalRoot = null;
        }
        window.removeEventListener('message', this.handleMessage);
        this.onCloseCallback();
    }
    handleMessage(event) {
        // [cite: 533-539] Handle Success/Failure messages
        const { type, data } = event.data;
        if (type === 'payment_success') {
            this.onSuccess(data);
            this.close();
        } else if (type === 'payment_failed') {
            this.onFailure(data);
        } else if (type === 'close_modal') {
            this.close();
        }
    }
}

export default PaymentGateway;