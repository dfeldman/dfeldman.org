// Hoverbox: Shows a div when you hover over a link.
// Used for citations, footnotes, and outbound links. 
// The div can contain just a title, or a title and an iframe,
// or a title and an image (which is used for PDF previews). 
// Related styles are in hover.css.
// There are also some special things for academic citations (not sure
// if I'll use.)

// Use of hoverbox should be wrapped in shortcodes.

/* Example use 

        <p>Here's a <a href="#" class="hoverbox-trigger" data-hoverbox="hover1">simple hoverbox</a> with just a title.</p>
        
        <p>This one has <a href="#" class="hoverbox-trigger" data-hoverbox="hover2">scrollable content</a> that extends beyond the box.</p>
        
        <p>Here's a <a href="#" class="hoverbox-trigger" data-hoverbox="hover3">hoverbox with an image</a> that sizes to fit.</p>
        
        <p>And finally, an <a href="#" class="hoverbox-trigger" data-hoverbox="hover4">iframe example</a> showing external content.</p>

        <!-- Simple hoverbox -->
        <div id="hover1" class="hoverbox-content">
            <div class="hoverbox-title">
                Simple Title
                <button class="hoverbox-close">&times;</button>
            </div>
            <div class="hoverbox-body">
                This is a basic hoverbox with just some text.
            </div>
        </div>

        <!-- Scrollable content -->
        <div id="hover2" class="hoverbox-content hoverbox-scroll">
            <div class="hoverbox-title">
                Scrollable Content
                <button class="hoverbox-close">&times;</button>
            </div>
            <div class="hoverbox-body">
                <p>This is a longer piece of content that will scroll.</p>
                <p>Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas.</p>
                <p>Vestibulum tortor quam, feugiat vitae, ultricies eget, tempor sit amet, ante.</p>
                <p>Donec eu libero sit amet quam egestas semper. Aenean ultricies mi vitae est.</p>
                <p>Mauris placerat eleifend leo. Quisque sit amet est et sapien ullamcorper pharetra.</p>
                <p>Vestibulum erat wisi, condimentum sed, commodo vitae, ornare sit amet, wisi.</p>
                <p>Aenean fermentum, elit eget tincidunt condimentum, eros ipsum rutrum orci.</p>
            </div>
        </div>

        <!-- Image hoverbox -->
        <div id="hover3" class="hoverbox-content hoverbox-image">
            <div class="hoverbox-title">
                Image Example
                <button class="hoverbox-close">&times;</button>
            </div>
            <div class="hoverbox-body">
                <img src="/api/placeholder/600/400" alt="Example image">
            </div>
        </div>

        <!-- Iframe hoverbox -->
        <div id="hover4" class="hoverbox-content hoverbox-iframe">
            <div class="hoverbox-title">
                External Content
                <button class="hoverbox-close">&times;</button>
            </div>
            <div class="hoverbox-body">
                <iframe src="/api/placeholder/600/400"></iframe>
            </div>
        </div>
    </div>
*/


class Hoverbox {
    constructor() {
        this.currentBox = null;
        this.isHovering = false;
        this.isMobile = window.matchMedia('(max-width: 768px)').matches;
        this.overlay = document.querySelector('.hoverbox-overlay');
        this.init();
    }

    init() {
        // Add hover listeners to all triggers
        document.querySelectorAll('.hoverbox-trigger').forEach(trigger => {
            trigger.addEventListener('mouseenter', () => {
                if (!this.isMobile) {
                    const boxId = trigger.dataset.hoverbox;
                    const box = document.getElementById(boxId);
                    if (box) {
                        this.isHovering = true;
                        this.show(trigger, box);
                    }
                }
            });

            trigger.addEventListener('mouseleave', (e) => {
                if (!this.isMobile) {
                    this.isHovering = false;
                    setTimeout(() => {
                        if (!this.isHovering) {
                            this.hide();
                        }
                    }, 100);
                }
            });

            // Mobile click handling
            trigger.addEventListener('click', (e) => {
                if (this.isMobile) {
                    e.preventDefault();
                    const boxId = trigger.dataset.hoverbox;
                    const box = document.getElementById(boxId);
                    if (box) {
                        this.show(trigger, box);
                        this.overlay.classList.add('hoverbox-visible');
                    }
                }
            });
        });

        document.querySelectorAll('.hoverbox-content').forEach(box => {
            box.addEventListener('mouseenter', () => {
                if (!this.isMobile) {
                    this.isHovering = true;
                }
            });

            box.addEventListener('mouseleave', () => {
                if (!this.isMobile) {
                    this.isHovering = false;
                    setTimeout(() => {
                        if (!this.isHovering) {
                            this.hide();
                        }
                    }, 100);
                }
            });
        });

        // Close button and overlay handling
        document.querySelectorAll('.hoverbox-close').forEach(closeBtn => {
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.hide();
                this.overlay.classList.remove('hoverbox-visible');
            });
        });

        this.overlay.addEventListener('click', () => {
            this.hide();
            this.overlay.classList.remove('hoverbox-visible');
        });

        window.addEventListener('resize', () => {
            this.isMobile = window.matchMedia('(max-width: 768px)').matches;
        });

        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hide();
                this.overlay.classList.remove('hoverbox-visible');
            }
        });
    }

    show(trigger, box) {
        if (this.currentBox) {
            this.hide();
        }

        this.currentBox = box;
        box.classList.add('hoverbox-visible');
        
        if (!this.isMobile) {
            this.position(trigger, box);
        }
    }

    hide() {
        if (this.currentBox) {
            this.currentBox.classList.remove('hoverbox-visible');
            this.currentBox = null;
        }
    }

    position(trigger, box) {
        // Get all the relevant rectangles and dimensions
        const triggerRect = trigger.getBoundingClientRect();
        const viewport = {
            top: window.scrollY,
            left: window.scrollX,
            width: window.innerWidth,
            height: window.innerHeight
        };

        // Reset box position to measure its natural dimensions
        box.style.top = '0';
        box.style.left = '0';
        const boxRect = box.getBoundingClientRect();

        // Remove existing notch if any
        const oldNotch = box.querySelector('.hoverbox-notch');
        if (oldNotch) oldNotch.remove();

        // Calculate available space in each direction
        const spaces = {
            below: viewport.height - triggerRect.bottom,
            above: triggerRect.top,
            right: viewport.width - triggerRect.right,
            left: triggerRect.left
        };

        // Try below first if there's enough room
        if (spaces.below >= boxRect.height + 6) {
            this.positionBox(box, 'below', trigger, boxRect);
            return;
        }

        // Find the direction with most space
        const bestSpace = Object.entries(spaces).reduce((best, [direction, space]) => {
            const spaceNeeded = (direction === 'above' || direction === 'below') 
                ? boxRect.height 
                : boxRect.width;
            
            if (space >= spaceNeeded && space > best.space) {
                return { direction, space };
            }
            return best;
        }, { direction: 'below', space: -1 });

        this.positionBox(box, bestSpace.direction, trigger, boxRect);
    }

    positionBox(box, direction, trigger, boxRect) {
        const triggerRect = trigger.getBoundingClientRect();
        const notch = document.createElement('div');
        notch.className = 'hoverbox-notch';

        let top, left;

        switch (direction) {
            case 'below':
                top = triggerRect.bottom + window.scrollY + 6;
                left = triggerRect.left + window.scrollX;
                notch.style.top = '-6px';
                notch.style.left = `${(triggerRect.width / 2) - 6}px`;
                break;
            
            case 'above':
                top = triggerRect.top + window.scrollY - boxRect.height - 6;
                left = triggerRect.left + window.scrollX;
                notch.style.bottom = '-6px';
                notch.style.left = `${(triggerRect.width / 2) - 6}px`;
                break;
            
            case 'right':
                top = triggerRect.top + window.scrollY;
                left = triggerRect.right + window.scrollX + 6;
                notch.style.left = '-6px';
                notch.style.top = `${(triggerRect.height / 2) - 6}px`;
                break;
            
            case 'left':
                top = triggerRect.top + window.scrollY;
                left = triggerRect.left + window.scrollX - boxRect.width - 6;
                notch.style.right = '-6px';
                notch.style.top = `${(triggerRect.height / 2) - 6}px`;
                break;
        }

        // Adjust horizontal position if box would go off-screen
        if (direction === 'below' || direction === 'above') {
            const rightOverflow = (left + boxRect.width) - window.innerWidth;
            if (rightOverflow > 0) {
                left -= rightOverflow;
                // Adjust notch position
                const notchLeft = parseFloat(notch.style.left) + rightOverflow;
                notch.style.left = `${notchLeft}px`;
            }
        }

        box.style.top = `${top}px`;
        box.style.left = `${left}px`;
        box.appendChild(notch);
    }
}

// Initialize when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
    window.hoverbox = new Hoverbox();
});