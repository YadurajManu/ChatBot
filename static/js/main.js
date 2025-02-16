$(document).ready(function() {
    // Initialize variables
    let currentMode = 'advisor';
    let isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    updateTheme(isDarkMode);
    updateCurrentMode(currentMode);

    // Event Handlers
    $('#sendButton').click(sendMessage);
    $('#userInput').keypress(function(e) {
        if (e.which == 13) sendMessage();
    });

    $('.mode-btn').click(function(e) {
        e.preventDefault();
        const mode = $(this).data('mode');
        changeMode(mode);
    });

    $('#helpButton').click(function(e) {
        e.preventDefault();
        showHelp();
    });

    // Commands Guide Button Handler
    $('#commandsButton').click(function(e) {
        e.preventDefault();
        new bootstrap.Modal($('#commandsModal')).show();
    });

    // Make commands clickable
    $(document).on('click', '.command-item', function() {
        const command = $(this).find('code').text();
        $('#userInput').val(command);
        $('#commandsModal').modal('hide');
        sendMessage();
    });

    $('.quick-command').click(function() {
        const command = $(this).data('command');
        handleQuickCommand(command);
    });

    $('.suggestion').click(function() {
        const text = $(this).text();
        $('#userInput').val(text);
        sendMessage();
    });

    $('#themeToggle').click(function() {
        isDarkMode = !isDarkMode;
        updateTheme(isDarkMode);
    });

    // Voice Input
    let isRecording = false;
    let recognition = null;
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onresult = function(event) {
            const text = event.results[0][0].transcript;
            $('#userInput').val(text);
            sendMessage();
        };
        
        recognition.onend = function() {
            isRecording = false;
            $('.voice-input').removeClass('recording');
        };
    }

    // Add voice input button
    $('.input-group').append(`
        <button class="voice-input">
            <i class="fas fa-microphone"></i>
        </button>
    `);

    $('.voice-input').click(function() {
        if (!recognition) {
            showToast('Speech recognition is not supported in your browser', 'warning');
            return;
        }
        
        if (!isRecording) {
            recognition.start();
            isRecording = true;
            $(this).addClass('recording');
        } else {
            recognition.stop();
            isRecording = false;
            $(this).removeClass('recording');
        }
    });

    // Context Menu
    let contextMenu = null;
    $(document).on('contextmenu', '.message', function(e) {
        e.preventDefault();
        
        if (contextMenu) {
            contextMenu.remove();
        }
        
        const isUserMessage = $(this).hasClass('user');
        contextMenu = $(`
            <div class="context-menu">
                <div class="context-menu-item copy-text">
                    <i class="fas fa-copy"></i>
                    Copy Text
                </div>
                ${!isUserMessage ? `
                    <div class="context-menu-item save-response">
                        <i class="fas fa-bookmark"></i>
                        Save Response
                    </div>
                    <div class="context-menu-item analyze-stock">
                        <i class="fas fa-chart-line"></i>
                        Analyze Stock
                    </div>
                ` : ''}
            </div>
        `);
        
        contextMenu.css({
            top: e.pageY + 'px',
            left: e.pageX + 'px'
        });
        
        $('body').append(contextMenu);
    });

    $(document).click(function() {
        if (contextMenu) {
            contextMenu.remove();
            contextMenu = null;
        }
    });

    // Context Menu Actions
    $(document).on('click', '.copy-text', function() {
        const text = $(this).closest('.context-menu')
            .prev('.message')
            .find('.message-text')
            .text();
        
        navigator.clipboard.writeText(text).then(() => {
            showToast('Text copied to clipboard', 'success');
        });
    });

    $(document).on('click', '.save-response', function() {
        const text = $(this).closest('.context-menu')
            .prev('.message')
            .find('.message-text')
            .text();
        
        // Save to localStorage
        const saved = JSON.parse(localStorage.getItem('savedResponses') || '[]');
        saved.push({
            text,
            timestamp: new Date().toISOString()
        });
        localStorage.setItem('savedResponses', JSON.stringify(saved));
        
        showToast('Response saved', 'success');
    });

    $(document).on('click', '.analyze-stock', function() {
        const text = $(this).closest('.context-menu')
            .prev('.message')
            .find('.message-text')
            .text();
        
        // Extract stock symbols using regex
        const symbols = text.match(/[A-Z]+(?:\.NS)?/g);
        if (symbols && symbols.length > 0) {
            $('#userInput').val(`analysis ${symbols[0]}`);
            sendMessage();
        } else {
            showToast('No stock symbol found in the message', 'warning');
        }
    });

    // Toast Notifications
    function showToast(message, type = 'info') {
        const toast = $(`
            <div class="toast ${type}">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 
                               type === 'warning' ? 'exclamation-triangle' : 
                               'info-circle'}"></i>
                ${message}
            </div>
        `);
        
        $('.toast-container').append(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // Theme Functions
    function updateTheme(dark) {
        document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
        $('#themeToggle i').attr('class', dark ? 'fas fa-moon' : 'fas fa-sun');
    }

    // Message Functions
    function sendMessage() {
        const userInput = $('#userInput').val().trim();
        if (!userInput) return;

        // Add user message
        addMessage(userInput, 'user');
        $('#userInput').val('');

        // Show typing indicator
        const typingIndicator = addTypingIndicator();

        // Send to backend
        $.ajax({
            url: '/api/command',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ command: userInput }),
            success: function(response) {
                // Remove typing indicator
                typingIndicator.remove();
                // Add bot response
                addMessage(formatResponse(response.response), 'bot');
                // Scroll to bottom
                scrollToBottom();
            },
            error: function() {
                typingIndicator.remove();
                addMessage('Sorry, I encountered an error processing your request.', 'bot');
            }
        });
    }

    function addMessage(content, sender) {
        const time = new Date().toLocaleTimeString();
        const message = $(`
            <div class="message ${sender}">
                <div class="message-content">
                    ${sender === 'bot' ? '<div class="message-header"><i class="fas fa-robot"></i><span>FinWise</span></div>' : ''}
                    <div class="message-text">${content}</div>
                    <div class="message-time">${time}</div>
                    <div class="message-actions">
                        <button class="message-action-btn copy-btn">
                            <i class="fas fa-copy"></i>
                        </button>
                        ${sender === 'bot' ? `
                            <button class="message-action-btn save-btn">
                                <i class="fas fa-bookmark"></i>
                            </button>
                            <button class="message-action-btn analyze-btn">
                                <i class="fas fa-chart-line"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `);
        
        $('#chatArea').append(message);
        scrollToBottom();
        return message;
    }

    function addTypingIndicator() {
        const indicator = $(`
            <div class="message bot">
                <div class="message-content">
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `);
        $('#chatArea').append(indicator);
        scrollToBottom();
        return indicator;
    }

    function handleQuickCommand(command) {
        let text = '';
        switch(command) {
            case 'price':
                text = 'price RELIANCE';
                break;
            case 'analysis':
                text = 'analysis TCS';
                break;
            case 'portfolio':
                text = 'show portfolio';
                break;
            case 'add':
                text = 'add stock RELIANCE 10 1000';
                break;
            case 'calculate':
                text = 'calculate sip 5000 10 12';
                break;
            case 'learn':
                text = 'learn stocks';
                break;
            case 'market':
                text = 'market mood';
                break;
            case 'news':
                text = 'latest market news';
                break;
            case 'watchlist':
                text = 'show watchlist';
                break;
        }
        $('#userInput').val(text);
        
        // Show toast with command description
        const descriptions = {
            price: 'Get real-time stock price',
            analysis: 'Technical analysis of a stock',
            portfolio: 'View your portfolio summary',
            add: 'Add a stock to your portfolio',
            calculate: 'Financial calculator',
            learn: 'Access learning resources',
            market: 'Check market sentiment',
            news: 'Get latest market news',
            watchlist: 'View your watchlist'
        };
        showToast(descriptions[command] || 'Command selected', 'info');
    }

    function changeMode(mode) {
        $.ajax({
            url: '/api/mode',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ mode: mode }),
            success: function(response) {
                currentMode = mode;
                updateCurrentMode(mode);
                addMessage(response.response, 'bot');
                
                // Update UI
                $('.mode-btn').removeClass('active');
                $(`.mode-btn[data-mode="${mode}"]`).addClass('active');
            }
        });
    }

    function showHelp() {
        $.ajax({
            url: '/api/help',
            success: function(response) {
                $('#helpContent').html(formatResponse(response.help));
                new bootstrap.Modal($('#helpModal')).show();
            }
        });
    }

    function scrollToBottom() {
        const chatArea = $('#chatArea');
        chatArea.scrollTop(chatArea[0].scrollHeight);
    }

    function updateCurrentMode(mode) {
        $('#currentMode').text($(`.mode-btn[data-mode="${mode}"] span`).text());
    }

    function formatResponse(response) {
        if (typeof response === 'string') {
            // Handle code blocks
            response = response.replace(/```(.*?)```/g, (match, code) => `
                <div class="code-block">
                    <button class="copy-code-btn">
                        <i class="fas fa-copy"></i>
                    </button>
                    <pre><code>${code}</code></pre>
                </div>
            `);
            
            // ... rest of the existing formatting ...
        }
        
        // Handle object responses
        if (typeof response === 'object') {
            // Handle error cases
            if (response.error) {
                return `❌ ${response.error}`;
            }
            
            // Format stock information
            if ('average_price' in response) {
                let output = `<div class="stock-info">`;
                output += `<div class="stock-header">📊 Stock Information</div>`;
                
                if (response.average_price !== 'N/A') {
                    output += `<div class="stock-price">₹${Number(response.average_price).toLocaleString('en-IN', {
                        maximumFractionDigits: 2,
                        minimumFractionDigits: 2
                    })}</div>`;
                } else {
                    output += `<div class="stock-price">N/A</div>`;
                }
                
                output += `<div class="stock-details">`;
                output += `<div class="detail"><span>Market Status:</span> ${response.market_status}</div>`;
                output += `<div class="detail"><span>Reliability:</span> ${response.reliability}</div>`;
                
                if (response.price_range && response.price_range.min !== 'N/A') {
                    output += `<div class="price-range">`;
                    output += `<div class="range-item"><span>High:</span> ₹${Number(response.price_range.max).toLocaleString('en-IN', {
                        maximumFractionDigits: 2,
                        minimumFractionDigits: 2
                    })}</div>`;
                    output += `<div class="range-item"><span>Low:</span> ₹${Number(response.price_range.min).toLocaleString('en-IN', {
                        maximumFractionDigits: 2,
                        minimumFractionDigits: 2
                    })}</div>`;
                    output += `</div>`;
                }
                
                if (response.sources && Object.keys(response.sources).length > 0) {
                    output += `<div class="source-details">`;
                    output += `<div class="source-header">Source Details</div>`;
                    for (const [source, info] of Object.entries(response.sources)) {
                        output += `<div class="source-group">`;
                        output += `<div class="source-name">${source.toUpperCase()}</div>`;
                        for (const [key, value] of Object.entries(info)) {
                            if (typeof value === 'number') {
                                if (key.toLowerCase().includes('price') || key.toLowerCase().includes('high') || key.toLowerCase().includes('low')) {
                                    output += `<div class="source-item"><span>${key}:</span> ₹${Number(value).toLocaleString('en-IN', {
                                        maximumFractionDigits: 2,
                                        minimumFractionDigits: 2
                                    })}</div>`;
                                } else if (key.toLowerCase().includes('volume')) {
                                    output += `<div class="source-item"><span>${key}:</span> ${Number(value).toLocaleString('en-IN')}</div>`;
                                } else {
                                    output += `<div class="source-item"><span>${key}:</span> ${value}</div>`;
                                }
                            } else {
                                output += `<div class="source-item"><span>${key}:</span> ${value}</div>`;
                            }
                        }
                        output += `</div>`;
                    }
                    output += `</div>`;
                }
                
                output += `</div>`; // Close stock-details
                output += `<div class="timestamp">Last Updated: ${response.timestamp}</div>`;
                output += `</div>`; // Close stock-info
                
                return output;
            }
            
            // Handle technical analysis response
            if (response.signals) {
                let output = `<div class="analysis-info">`;
                output += `<div class="analysis-header">📈 Technical Analysis</div>`;
                
                output += `<div class="signal-summary">`;
                for (const [key, value] of Object.entries(response.signals)) {
                    output += `<div class="signal-item">
                        <span>${key.charAt(0).toUpperCase() + key.slice(1)}:</span> 
                        <span class="signal-value ${value.toLowerCase()}">${value}</span>
                    </div>`;
                }
                output += `</div>`;
                
                if (response.indicators) {
                    output += `<div class="indicators">`;
                    output += `<div class="indicators-header">Key Indicators</div>`;
                    for (const [key, value] of Object.entries(response.indicators)) {
                        if (typeof value === 'number') {
                            output += `<div class="indicator-item"><span>${key}:</span> ${value.toFixed(2)}</div>`;
                        } else {
                            output += `<div class="indicator-item"><span>${key}:</span> ${value}</div>`;
                        }
                    }
                    output += `</div>`;
                }
                
                if (response.chart_path) {
                    output += `<div class="chart-container">
                        <iframe width="100%" height="400px" src="${response.chart_path}"></iframe>
                    </div>`;
                }
                
                output += `</div>`;
                return output;
            }
        }
        
        // Default case: return as is
        return response;
    }

    // Message Action Handlers
    $(document).on('click', '.copy-btn', function() {
        const text = $(this).closest('.message-content').find('.message-text').text();
        navigator.clipboard.writeText(text).then(() => {
            showToast('Text copied to clipboard', 'success');
        });
    });

    $(document).on('click', '.save-btn', function() {
        const text = $(this).closest('.message-content').find('.message-text').text();
        const saved = JSON.parse(localStorage.getItem('savedResponses') || '[]');
        saved.push({
            text,
            timestamp: new Date().toISOString()
        });
        localStorage.setItem('savedResponses', JSON.stringify(saved));
        showToast('Response saved', 'success');
    });

    $(document).on('click', '.analyze-btn', function() {
        const text = $(this).closest('.message-content').find('.message-text').text();
        const symbols = text.match(/[A-Z]+(?:\.NS)?/g);
        if (symbols && symbols.length > 0) {
            $('#userInput').val(`analysis ${symbols[0]}`);
            sendMessage();
        } else {
            showToast('No stock symbol found in the message', 'warning');
        }
    });

    // Copy Code Button Handler
    $(document).on('click', '.copy-code-btn', function() {
        const code = $(this).siblings('pre').text();
        navigator.clipboard.writeText(code).then(() => {
            showToast('Code copied to clipboard', 'success');
        });
    });
}); 