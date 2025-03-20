function showmsg(user, message) {
    alert(user + ' ' + message);
}
document.addEventListener('DOMContentLoaded', function () {


    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // 高亮显示拖放区域
    function highlight(e) {
        document.body.classList.add('highlight');
    }

    // 取消高亮显示
    function unhighlight(e) {
        document.body.classList.remove('highlight');
    }

    // 处理文件拖放事件
    function handleDrop(e) {
        let dt = e.dataTransfer;
        let files = dt.files;

        handleFiles(files);
    }
    
    //处理音频文件  20250111
    const startRecordingButton = document.getElementById('start-recording');
    const stopRecordingButton = document.getElementById('stop-recording');

    let mediaRecorder;
    let audioChunks = [];

    // 开始录音
    startRecordingButton.addEventListener('click', async () => {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);  // 收集音频数据
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const audioFile = new File([audioBlob], 'audio.wav', { type: 'audio/wav' });
            sendAudioToBackend(audioFile);  // 将音频文件发送到后端
            audioChunks.length = 0
        };

        mediaRecorder.start();
        startRecordingButton.style.display = 'none';
        stopRecordingButton.style.display = 'inline';
    });

    // 停止录音
    stopRecordingButton.addEventListener('click', () => {
        mediaRecorder.stop();
        stopRecordingButton.style.display = 'none';
        startRecordingButton.style.display = 'inline';
    });

    // 将音频发送到后端
    async function sendAudioToBackend(audioFile) {
        const formData = new FormData();
        formData.append('audio', audioFile);  // 将音频文件添加到表单数据中
        const messageInput = document.getElementById('message-input');
        messageInput.value = "";
        // 发送到后端的API
        const response = await fetch('/backend-api/v2/audioconver', {
            method: 'POST',
            body: formData,
        });
        console.log(response);  // 检查响应对象
        const text = await response.text(); 
        console.log("Raw response:", text); // 打印返回的原始数据
        messageInput.value = text;  // 填充识别结果
        triggerEnterKey(messageInput);  // 自动回车发送
        }
    // 模拟回车键触发发送
    function triggerEnterKey(textarea) {
        // 创建一个键盘事件，模拟回车键按下
        const enterEvent = new KeyboardEvent('keydown', {
            key: 'Enter',
            code: 'Enter',
            keyCode: 13,
            charCode: 13,
            bubbles: true,
        });
        // 触发事件，模拟用户按下回车键
        textarea.dispatchEvent(enterEvent);
    }

    //处理音频文件结束


    uploadedFiles = []
    // 处理文件
    function handleFiles(files) {
        const fileList = document.getElementById('file-info');
        fileList.innerHTML = "";
        fileList.style.display = "flex"; // Set flexbox layout for horizontal alignment
        fileList.style.flexWrap = "wrap"; // Allow wrapping if too many images
        fileList.style.gap = "10px"; // Add space between images
        fileList.style.justifyContent = "center"; // Center align images horizontally

        Array.from(files).forEach(file => {
            uploadedFiles.push(file); // Add file to the global array
            // const fileType = getFileTypeIcon(file);1
            // const listItem = document.createElement('li');
            // listItem.innerHTML = `${fileType} ${file.name}`;
            // fileList.appendChild(listItem);
            const fileReader = new FileReader();
            fileReader.onload = function(event) {
                const imgContainer = document.createElement('div');
                imgContainer.classList.add('image-container');
                imgContainer.style.position = "relative";

                const img = document.createElement('img');
                img.src = event.target.result;
                img.classList.add('thumbnail');
                img.style.width = "150px"; // Set fixed width for thumbnails
                img.style.height = "80px"; // Set fixed height for thumbnails
                img.style.objectFit = "cover"; // Ensure proper aspect ratio

                const closeButton = document.createElement('span');
                closeButton.textContent = '×';
                closeButton.classList.add('close-btn');
                closeButton.style.position = "absolute";
                closeButton.style.top = "5px";
                closeButton.style.right = "5px";
                closeButton.style.cursor = "pointer";
                closeButton.style.background = "rgba(0, 0, 0, 0.5)";
                closeButton.style.color = "white";
                closeButton.style.borderRadius = "50%";
                closeButton.style.width = "20px";
                closeButton.style.height = "20px";
                closeButton.style.display = "flex";
                closeButton.style.alignItems = "center";
                closeButton.style.justifyContent = "center";
                closeButton.addEventListener('click', function () {
                    imgContainer.remove(); // Remove image when clicked
                });

                imgContainer.appendChild(img);
                imgContainer.appendChild(closeButton);
                fileList.appendChild(imgContainer);
            };

            if (file.type.startsWith('image')) {
                fileReader.readAsDataURL(file);
            }
        });
        
        file = uploadedFiles
        console.log("Uploaded files array:", uploadedFiles);

    }

    

    function getFileTypeIcon(file) {
        let fileType;
        if (file.type.startsWith('text') || file.name.endsWith('.log')) {
            if (file.type.includes('python')) {
                fileType = '🐍';
            } else if (file.type.includes('javascript') || file.type.includes('html') || file.type.includes('css')) {
                fileType = '📜';
            } else if (file.type.includes('java')) {
                fileType = '☕';
            } else {
                fileType = '📄';
            }
        } else if (file.type.startsWith('image')) {
            fileType = '🖼️';
        } else if (file.name.endsWith('.pdf')) {
            fileType = '📙';
        } else if (file.name.endsWith('.docx')) {
            fileType = '📘';
        } else {
            fileType = '❓';
        }
        return fileType;
    }
    
    //处理文件上传
    // const fileInput = document.getElementById("file-upload");
    // const uploadButton = document.getElementById("upload-button");
    // const docList = document.getElementById("doc-list");
    // const vectorDBSelect = document.getElementById("vectordb");

    // fileInput.addEventListener("change", function (event) {
    //     console.log(event.target.files);
    //     handleDocFiles(event.target.files);
    // });

    // uploadButton.addEventListener("click", function () {
    //     console.log("上传按钮被点击");
    //     uploadFiles();
    // });

    // function handleDocFiles(files) {
    //     docList.innerHTML = "";
    //     Array.from(files).forEach(file => {
    //         const listItem = document.createElement("li");
    //         listItem.textContent = file.name+'llll';
    //         docList.appendChild(listItem);
    //     });
    //     console.log('doc files',files)

    // }

    // async function uploadFiles() {
    //     const files = fileInput.files;
    //     if (files.length === 0) {
    //         alert("请选择要上传的文件");
    //         return;
    //     }

    //     const formData = new FormData();
    //     for (let file of files) {
    //         formData.append("files", file);
    //     }
    //     formData.append("category", vectorDBSelect.value); // 选择分类

    //     console.log('doc files',file)

    // }

    // 重置页面
    function resetPage() {
        file = null;
        document.getElementById('file-info').innerHTML = '';
        document.getElementById('file-prompt').classList.remove('hidden');
        document.getElementById('file-label').classList.remove('hidden');
        document.getElementById('text-content').style.display = 'none';
        document.getElementById('image-content').style.display = 'none';
        document.getElementById('text-content').value = '';
        document.getElementById('image-content').src = '';
    }

    // 为整个文档添加拖放事件监听器
    document.addEventListener('dragenter', preventDefaults, false);
    document.addEventListener('dragover', preventDefaults, false);
    document.addEventListener('dragleave', preventDefaults, false);
    document.addEventListener('drop', preventDefaults, false);

    document.addEventListener('dragenter', highlight, false);
    document.addEventListener('dragover', highlight, false);
    document.addEventListener('dragleave', unhighlight, false);
    document.addEventListener('drop', unhighlight, false);


    document.addEventListener('drop', (e) => {
        handleDrop(e);
        document.body.classList.remove('highlight');
    }, false)

    //document.addEventListener('drop', handleDrop, false);

    const CUSTOM_KEYWORDS = [
        'tablespace', 'extend'];

    hljs.getLanguage('bash').keywords.built_in.push(...CUSTOM_KEYWORDS);

    function getRandomEmoji() {
        const emojiList = [
            '🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐻‍❄️', '🐨', '🐯', '🦁', '🐮', '🐷', '🐽', '🐸', '🐵', '🙈', '🙉', '🙊',
            '🐒', '🐔', '🐧', '🐦', '🐤', '🐣', '🐥', '🦆', '🦅', '🦉', '🦇', '🐺', '🐗', '🐴', '🦄', '🐝', '🐛', '🦋', '🐌', '🐞',
            '🐜', '🦟', '🦗', '🕷', '🕸', '🦂', '🐢', '🐍', '🦎', '🦖', '🦕', '🐙', '🦑', '🦐', '🦞', '🦀', '🐡', '🐠', '🐟', '🐬',
            '🐳', '🐋', '🦈', '🐊', '🐅', '🐆', '🦓', '🦍', '🦧', '🦣', '🐘', '🦛', '🦏', '🐪', '🐫', '🦒', '🦘', '🐃', '🐂', '🐄',
            '🐎', '🐖', '🐏', '🐑', '🦙', '🐐', '🦌', '🐕', '🐩', '🦮', '🐕‍🦺', '🐈', '🐈‍⬛', '🐓', '🦃', '🦚', '🦜', '🦢', '🦩',
            '🕊', '🐇', '🦝', '🦨', '🦡', '🦦', '🦥', '🐁', '🐀', '🐿', '🦔', '🐾', '🐉', '🐲', '🌵', '🎄', '🌲', '🌳', '🌴', '🌱',
            '🌿', '☘️', '🍀', '🎍', '🎋', '🍃', '🍂', '🍁', '🍄', '🐚', '💐', '🌷', '🌹', '🥀', '🌺', '🌸', '🌼', '🌻', '🌞', '🌝',
            '🌛', '🌜', '🌚', '🌕', '🌖', '🌗', '🌘', '🌑', '🌒', '🌓', '🌔', '🌙', '🌎', '🌍', '🌏', '🪐', '💫', '⭐️', '🌟', '✨',
            '⚡️', '☄️', '💥', '🔥', '🌪', '🌈', '☀️', '🌤', '⛅️', '🌥', '☁️', '🌦', '🌧', '⛈', '🌩', '🌨', '❄️', '☃️', '⛄️',
            '🌬', '💨', '💧', '💦', '☔️', '☂️', '🌊', '🌫', '🍏', '🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍈', '🍒', '🍑',
            '🥭', '🍍', '🥥', '🥝', '🍅', '🍆', '🥑', '🥦', '🥬', '🥒', '🌶', '🌽', '🥕', '🧄', '🧅', '🥔', '🍠', '🥐', '🥯', '🍞',
            '🥖', '🥨', '🧀', '🥚', '🍳', '🧈', '🥞', '🧇', '🥓', '🥩', '🍗', '🍖', '🦴', '🌭', '🍔', '🍟', '🍕', '🥪', '🥙', '🧆',
            '🌮', '🌯', '🥗', '🥘', '🍝', '🍜', '🍲', '🍛', '🍣', '🍱', '🥟', '🦪', '🍤', '🍙', '🍚', '🍘', '🍥', '🥠', '🥮', '🍢',
            '🍡', '🍧', '🍨', '🍦', '🥧', '🧁', '🍰', '🎂', '🍮', '🍭', '🍬', '🍫', '🍿', '🍩', '🍪', '🌰', '🥜', '🍯', '🥛', '🍼',
            '☕️', '🍵', '🧃', '🥤', '🍶', '🍺', '🍻', '🥂', '🍷', '🥃', '🍸', '🍹', '🧉', '🍾', '🧊', '🥄', '🍴', '🍽', '🥣', '🥡',
            '🥢', '🧂', '🚗', '🚕', '🚙', '🚌', '🚎', '🏎', '🚓', '🚑', '🚒', '🚐', '🚚', '🚛', '🚜', '🦯', '🦽', '🦼', '🛴',
            '🚲', '🛵', '🏍', '🛺', '🚨', '🚔', '🚍', '🚘', '🚖', '🚡', '🚠', '🚟', '🚃', '🚋', '🚞', '🚝', '🚄', '🚅', '🚈', '🚂',
            '🚆', '🚇', '🚊', '🚉', '✈️', '🛫', '🛬', '🛩', '💺', '🛰', '🚀', '🛸', '🚁', '🛶', '⛵️', '🚤', '🛥', '🛳', '⛴', '🚢',
            '⚓️', '⛽️', '🚧', '🚦', '🚥', '🚏', '🗺', '🗿', '🗽', '🗼', '🏰', '🏯', '🏟', '🎡', '🎢', '🎠', '⛲️', '⛱', '🏖', '🏝',
            '🏜', '🌋', '⛰', '🏔', '🗻', '🏕', '⛺️', '🏠', '🏡', '🏘', '🏚', '🏗', '🏭', '🏢', '🏬', '🏣', '🏤', '🏥', '🏦', '🏨',
            '🏪', '🏫', '🏩', '💒', '🏛', '⛪️', '🕌', '🕍', '🛕', '🕋', '⛩', '🛤', '🛣', '🗾', '🎑', '🏞', '🌅', '🌄', '🌠', '🎇',
            '🎆', '🌇', '🌆', '🏙', '🌃', '🌌', '🌉', '🌁', '⚽️', '🏀', '🏈', '⚾️', '🥎', '🎾', '🏐', '🏉', '🥏', '🎱', '🪀', '🏓', '🏸', '🏒', '🏑', '🥍', '🏏', '🪃', '🥅', '⛳️', '🪁', '🏹', '🎣', '🤿', '🥊', '🥋', '🎽', '🛹', '🛼', '🛷', '⛸', '🥌', '🎿', '⛷', '🏂', '🪂', '🏋️‍♀️', '🏋️', '🏋️‍♂️', '🤼‍♀️', '🤼', '🤼‍♂️', '🤸‍♀️', '🤸', '🤸‍♂️', '⛹️‍♀️', '⛹️', '⛹️‍♂️', '🤺', '🤾‍♀️', '🤾', '🤾‍♂️', '🏌️‍♀️', '🏌️', '🏌️‍♂️', '🏇', '🧘‍♀️', '🧘', '🧘‍♂️', '🏄‍♀️', '🏄', '🏄‍♂️', '🏊‍♀️', '🏊', '🏊‍♂️', '🤽‍♀️', '🤽', '🤽‍♂️', '🚣‍♀️', '🚣', '🚣‍♂️', '🧗‍♀️', '🧗', '🧗‍♂️', '🚵‍♀️', '🚵', '🚵‍♂️', '🚴‍♀️', '🚴', '🚴‍♂️', '🏆', '🥇', '🥈', '🥉', '🏅', '🎖', '🏵', '🎗', '🎫', '🎟', '🎪', '🤹', '🤹‍♂️', '🤹‍♀️', '🎭', '🩰', '🎨', '🎬', '🎤', '🎧', '🎼', '🎹', '🥁', '🪘', '🎷', '🎺', '🪗', '🎸', '🪕', '🎻', '🎲', '♟', '🎯', '🎳', '🎮', '🎰', '🧩'
        ];
        return emojiList[Math.floor(Math.random() * emojiList.length)];
    }

    function getRandomEmojis(count) {
        let emojis = '';
        for (let i = 0; i < count; i++) {
            emojis += getRandomEmoji();
        }
        return emojis;
    }

    const pElement = document.querySelector('.welcome-message p');
    pElement.innerHTML = getRandomEmojis(5) + '<br>' + lang['welcome-msg']  ;

    // document.getElementById('Temperature').addEventListener('input', function () {
    //     document.getElementById('temperatureValue').textContent = this.value;
    // });

    // 显示欢迎消息
    const welcomeMessage = document.getElementById('welcome-message');
    welcomeMessage.style.display = 'block';

    // 隐藏欢迎消息
    //document.addEventListener('click', function () {
    //     welcomeMessage.style.display = 'none';
    // }, { once: true });



    document.getElementById('message-input').addEventListener('keydown', function (event) {
        //console.log("监控到"+event.key)
        if (event.key === 'Enter') {
            welcomeMessage.style.display = 'none';
            // 这里可以添加发送消息的逻辑
            // const fileInfo = document.getElementById('file-info');
            // fileInfo.innerHTML = ``
            document.getElementById('file-info').innerHTML = ''
        }
    });

    document.getElementById('send-button').addEventListener('click', function () {
        welcomeMessage.style.display = 'none';
        // 这里可以添加发送消息的逻辑
        const fileInfo = document.getElementById('file-info');
        fileInfo.innerHTML = ``
    });

    // Toggle conversation visibility
    const toggleButton = document.getElementById('toggleButton');
    const conversationsBox = document.querySelector('.box.conversations');
    let originalStyles = getComputedStyle(conversationsBox).cssText;

    toggleButton.addEventListener('click', function () {
        if (conversationsBox.style.display === 'none') {
            conversationsBox.style.cssText = originalStyles;
            toggleButton.innerHTML = '<i class="fa fa-chevron-circle-left" aria-hidden="true"></i>';
        } else {
            originalStyles = conversationsBox.style.cssText;
            conversationsBox.style.display = 'none';
            toggleButton.innerHTML = '<i class="fa fa-chevron-circle-right" aria-hidden="true"></i>';
        }
    });
});
document.addEventListener('DOMContentLoaded', function() {
    // ... existing code ...

    // 导航方块处理
    const navBlocks = document.querySelectorAll('.nav-block');
    let currentValue = 'image_to_text'; // 默认值

    // 确保初始化时设置正确的激活状态
    function initializeNavBlocks() {
        navBlocks.forEach(block => {
            if(block.dataset.value === currentValue) {
                block.classList.add('active');
            } else {
                block.classList.remove('active');
            }
        });
        // 初始化时更新UI
        updateUIForMode(currentValue);
    }

    // 页面加载完成后立即初始化
    initializeNavBlocks();

    // 初始化选中状态
    navBlocks.forEach(block => {
        if(block.dataset.value === currentValue) {
            block.classList.add('active');
        }
    });

    // 点击事件处理
    navBlocks.forEach(block => {
        block.addEventListener('click', function() {
            // 移除所有active类
            navBlocks.forEach(b => b.classList.remove('active'));
            // 添加active类到当前点击的方块
            this.classList.add('active');
            // 更新当前值
            currentValue = this.dataset.value;
            
            // 更新UI显示
            updateUIForMode(currentValue);
        });
    });

    // 根据不同模式更新UI显示
    function updateUIForMode(mode) {
        const messageInput = document.getElementById('message-input');
        const fileInfo = document.getElementById('file-info');

        switch(mode) {
            case 'image_to_text':
                messageInput.placeholder = '请上传图片或输入问题...';
                fileInfo.style.display = 'block';
                break;
            case 'ora_awr':
                messageInput.placeholder = '请上传OEM告警信息或输入分析要求...';
                fileInfo.style.display = 'block';
                break;
            case 'ora_doc':
                messageInput.placeholder = '请输入数据库相关问题...';
                fileInfo.style.display = 'none';
                break;
            case 'ora_check':  // 添加新的模式
                messageInput.placeholder = '请输入巡检相关问题...';
                fileInfo.style.display = 'block';
            case 'data_analysis':
                messageInput.placeholder = '请上传CSV文件...';
                fileInfo.style.display = 'block';
            break;
        }
    }

    // 初始化UI显示
    updateUIForMode(currentValue);
});
document.getElementById('memory').addEventListener('input', function () {
    var memoryValue = document.getElementById('memory').value;
    document.getElementById('memoryvalue').textContent = memoryValue;
});

const prompts = [
    "/image A serene Japanese garden with cherry blossom trees in full bloom and a traditional tea house in the background.",
    "/image A cyberpunk cityscape at night, with neon lights reflecting off the rain-soaked streets and futuristic vehicles zooming by.",
    "/image A whimsical anime character with bright pink hair, large expressive eyes, and a magical staff standing in a mystical forest.",
    "/image A majestic mountain range with a crystal-clear lake at its base, reflecting the snow-capped peaks and a clear blue sky.",
    "/image A cozy, modern living room with large windows, minimalist furniture, and a fireplace, exuding warmth and comfort.",
    "/image A mythical dragon soaring through the clouds, with golden scales and fiery breath, over a medieval castle.",
    "An intricate gothic cathedral with towering spires, detailed stained glass windows, and a dramatic sunset behind it.",
    "/image A futuristic astronaut exploring a colorful alien planet, surrounded by bizarre flora and fauna under a vibrant sky.",
    "/image A peaceful beach scene with turquoise waters, white sand, and a hammock between two palm trees swaying in the breeze.",
    "/image A charming, rustic cottage in the countryside, surrounded by lush gardens, a stone path, and a thatched roof.",
    "/image A fantasy world with floating islands, cascading waterfalls, and ancient ruins hidden among dense, enchanted forests.",
    "/image A vibrant carnival scene with colorful tents, lively performers, and a giant Ferris wheel lit up against the night sky.",
    "/image A group of diverse video game characters in a dynamic action pose, ready to embark on an epic quest.",
    "/image A romantic Parisian street at dusk, with quaint cafés, cobblestone paths, and the Eiffel Tower in the distance.",
    "/image A serene mountain cabin in the winter, surrounded by snow-covered pine trees and a frozen lake reflecting the moonlight.",
    "/image A magical underwater kingdom with mermaids, shimmering sea creatures, and ancient shipwrecks covered in coral.",
    "/image A bustling market in Marrakech, with vibrant textiles, aromatic spices, and a mix of traditional and modern architecture.",
    "/image A sci-fi lab with advanced robotics, holographic displays, and scientists in sleek, futuristic uniforms conducting experiments.",
    "/image A tranquil Zen garden with carefully raked sand, bonsai trees, and a stone pathway leading to a bamboo gate.",
    "/image A joyous festival celebrating life, with colorful lanterns, traditional dances, and people enjoying delicious street food.",
    "/image Beautiful rural scenery, lakes, animals and nature in harmony, artistic, oil painting, master works",
    "/image An ancient Roman coliseum bathed in golden sunlight, with gladiators preparing for battle in the arena's center.",
    "/image A scene from a classic film noir, with a detective in a trench coat and fedora, under a dimly lit streetlamp in a misty alley.",
    "/image A breathtaking view of a distant galaxy, with swirling nebulas and clusters of stars, seen from the edge of a space station.",
    "/image A futuristic cityscape on a distant planet, with sleek skyscrapers, hovering vehicles, and alien flora in the background.",
    "/image An erupting volcano with lava flowing down its sides, ash clouds billowing into the sky, and a village in the distance.",
    "/image A serene Antarctic landscape with towering icebergs, a colony of penguins, and the aurora borealis illuminating the sky.",
    "/image A powerful tornado tearing through a small town, with debris swirling in the air and dark, ominous clouds overhead.",
    "/image A vibrant underwater world teeming with colorful coral reefs, exotic fish, and a majestic whale gliding through the depths.",
    "/image A playful scene with various pets, including cats, dogs, and birds, in a cozy home setting with warm lighting.",
    "/image A dynamic anime battle between two powerful warriors, with energy blasts and dramatic poses in a stylized cityscape.",
    "/image A serene Chinese ink painting depicting a misty mountain range, with delicate brush strokes and minimalist composition.",
    "/image A reinterpretation of Vincent van Gogh's 'Starry Night,' with swirling blue hues and a glowing crescent moon.",
    "/image A mystical scene with a majestic dragon soaring over an ancient castle, surrounded by mist and moonlight.",
    "/image A famous historical landmark like the Great Wall of China, stretching across the landscape with a stunning sunset in the background.",
    "/image A sci-fi scene featuring a sleek spaceship landing on a mysterious, uncharted planet with towering alien structures.",
    "/image A dramatic depiction of a stormy ocean with a lighthouse standing tall against the crashing waves and lightning strikes.",
    "/image A charming depiction of an old European village, with cobblestone streets, colorful houses, and blooming flowers.",
    "/image A fantastical scene of a medieval knight in shining armor facing a fierce dragon amidst a dark, enchanted forest.",
    "/image A whimsical portrait of a beloved movie character, like a mischievous cat from a fantasy world, in a magical setting.",
    "/image An impressionist-style painting of a bustling Parisian café, with vibrant colors and lively crowds enjoying the evening."
];
outputsatisfied = ''
// function toggleThumbs(thumb) {
    
//     const thumbsUp = document.getElementById('thumbs-up');
//     const thumbsDown = document.getElementById('thumbs-down');

//     if (thumb === 'up') {
//         //console.log('testtest')
//         outputsatisfied = '我对你这个答案满意，但请再次回答。'
        
//         thumbsUp.classList.add('icon-highlight');   // 给点赞图标添加高亮
//         thumbsDown.classList.remove('icon-highlight'); // 移除批评图标的高亮
//         thumbsUp.classList.remove('icon-gray');
//         thumbsDown.classList.add('icon-gray');
//     } else if (thumb === 'down') {
//         outputsatisfied = '我对你这个答案不满意，但请再次回答。'
//         thumbsDown.classList.add('icon-highlight'); // 给批评图标添加高亮
//         thumbsUp.classList.remove('icon-highlight');   // 移除点赞图标的高亮
//         thumbsUp.classList.add('icon-gray');
//         thumbsDown.classList.remove('icon-gray');
//     }
// }

document.addEventListener('click', function (event) {
    const target = event.target;

    // 检查点击的是否是点赞或批评的图标
    if (target.classList.contains('fa-thumbs-o-up') || target.classList.contains('fa-thumbs-o-down')) {
        const thumbsUp = target.classList.contains('fa-thumbs-o-up') ? target : target.previousElementSibling;
        const thumbsDown = target.classList.contains('fa-thumbs-o-down') ? target : target.nextElementSibling;

        if (target.classList.contains('fa-thumbs-o-up')) {
             
            thumbsUp.classList.add('icon-highlight');
            thumbsUp.classList.remove('icon-gray');
            thumbsDown.classList.add('icon-gray');
            thumbsDown.classList.remove('icon-highlight');
        } else {
             
            thumbsDown.classList.add('icon-highlight');
            thumbsDown.classList.remove('icon-gray');
            thumbsUp.classList.add('icon-gray');
            thumbsUp.classList.remove('icon-highlight');
        }
    }
});

function getRandomQuestion3() {
    const randomIndex = Math.floor(Math.random() * prompts.length);
    return prompts[randomIndex];
}

const emojiBox = document.getElementById('image_exmaple');

// 添加点击事件监听器
emojiBox.addEventListener('click', () => {
    // 获取textarea元素
    console.log(1)
    const messageInput = document.getElementById('message-input');

    // 设置textarea的值
    messageInput.value = getRandomQuestion3();
});

const questions2 = [
    "请帮我编写一段调用大模型问答的Transformer代码",
    "请编写一段Oracle翻页查询的SQL",
    "请帮我编写一段Oracle PL/SQL用于写入数据到本地文件系统的例子",
    "请帮我编写一个简单Flask Web应用的代码例子",
    "帮我编写一个JAVA如何实现冒泡排序的例子",
    "帮我编写一段Python，如何进行llama微调的的例子",
    "帮我编写一段c代码，用于读取bios的基本信息",
    "帮我编写一段shell代码，可以检查服务器的cpu,内存，进程数的资源占用"
]
function getRandomQuestion2() {
    const randomIndex = Math.floor(Math.random() * questions2.length);
    return questions2[randomIndex];
}

const codeBox = document.getElementById('codeanalysis');

// 添加点击事件监听器
codeBox.addEventListener('click', () => {
    // 获取textarea元素
    //console.log(1)
    const messageInput = document.getElementById('message-input');

    // 设置textarea的值
    messageInput.value = getRandomQuestion2();
});

const questions = [
    "世界上最高的山峰是什么？告诉我它的详细信息",
    "太阳系中最大的行星是哪个？",
    "谁是相对论的提出者？",
    "人类首次登月是在什么时候？",
    "水的化学分子式是什么？",
    "中国的首都是哪座城市？它在历史上曾经是哪个朝代的首都?",
    "二战期间，哪个国家投降导致战争结束？",
    "光伏市场的竞争情况和前景预估？",
    "谈谈新西兰的畜牧业的可持续发展？",
    "银行发放贷款前的资产评估，应该怎么做？",
    "目前世界上最先进的变电技术有哪些？",
    "太阳系各大行星的空气中的气体是什么？",
    "世界上最大的海洋是哪一个？",
    "计算机的中央处理单元简称是什么？",
    "植物进行光合作用需要什么？",
    "大模型的训练为什么依赖GPU，而为什么AMD公司的GPU通常不能用于训练?",
    "上市公司为什么需要定期公布财报？",
    "编程解答，如何快速的从判断一个元素不存在于另外一个数组？",
    "国际象棋的棋盘有多少个格子？",
    "日本房地产在90年代崩盘的原因是什么？",
    "新能源汽车常用的电池有几种，它们各种的成分，以及优缺点是什么，请给出详细说明"
];

function getRandomQuestion() {
    const randomIndex = Math.floor(Math.random() * questions.length);
    return questions[randomIndex];
}

const generalask = document.getElementById('generalask');

// 添加点击事件监听器
generalask.addEventListener('click', () => {
    // 获取textarea元素
    //console.log(1)
    const messageInput = document.getElementById('message-input');

    // 设置textarea的值
    messageInput.value = getRandomQuestion();
});

document.addEventListener('DOMContentLoaded', function () {
    var switchRag = document.getElementById('switch_rag');
    var inputContainers = document.querySelectorAll('.input-container');
    var knowledgebase = document.getElementById('knowledgebase');
    knowledgebase
    function toggleInputContainers() {
        if (switchRag.checked) {
            inputContainers.forEach(function (container) {
                container.style.display = 'block';
            });
            knowledgebase.style = 'height: fit-content;display: flex;align-items: center;gap: 16px;padding-right: 15px';

        } else {
            inputContainers.forEach(function (container) {
                container.style.display = 'none';
            });
            knowledgebase.style.display = 'none';
        }
    }

    // 初始化状态
    toggleInputContainers();

    // 监听开关变化
    switchRag.addEventListener('change', toggleInputContainers);
});
const lightIcon = document.getElementById('light-icon');
const darkIcon = document.getElementById('dark-icon');
lightIcon.addEventListener('click', () => {
    document.documentElement.style.setProperty('--colour-1', 'rgb(100, 100, 100)');//--大背景
    document.documentElement.style.setProperty('--accent', 'rgb(100, 100, 100)');//--大背景
    document.documentElement.style.setProperty('--blur-bg', 'rgb(45, 45, 45)');//--左侧bar
    document.documentElement.style.setProperty('--boxmain', 'rgb(73, 73, 73)');//--消息主窗
    document.documentElement.style.setProperty('--colour-3', 'rgb(252, 153, 5)');//--字体
    lightIcon.style.display = 'none';
    darkIcon.style.display = 'inline';
});
darkIcon.addEventListener('click', () => {
    document.documentElement.style.setProperty('--colour-1', '#ffffff');
    document.documentElement.style.setProperty('--accent', '#ffffff');
    document.documentElement.style.setProperty('--blur-bg', '#f4f4f4');
    document.documentElement.style.setProperty('--boxmain', '#ffffff');
    document.documentElement.style.setProperty('--colour-3', 'rgb(35, 35, 35)');//--字体
    lightIcon.style.display = 'inline';
    darkIcon.style.display = 'none';
});
document.addEventListener('click', function (event) {
    if (event.target.tagName === 'IMG' && event.target.closest('.content')) {
        event.target.classList.toggle('zoomed');
    }
});
//添加图片放大功能 2025-01-10
document.addEventListener('click', function (event) {
    if (event.target.tagName === 'IMG' && event.target.closest('.image-content')) {
        event.target.classList.toggle('zoomed');
    }
});

document.getElementById('decrement').addEventListener('click', function () {
    var input = document.getElementById('Temperature');
    var value = parseFloat(input.value);
    if (value > 0) {
        input.value = (value - 0.1).toFixed(1);
    }
});
document.getElementById('increment').addEventListener('click', function () {
    var input = document.getElementById('Temperature');
    var value = parseFloat(input.value);
    if (value < 1) {
        input.value = (value + 0.1).toFixed(1);
    }
});
document.getElementById('decrement_topk').addEventListener('click', function () {
    var input = document.getElementById('vdb_topk');
    var value = parseFloat(input.value);
    if (value > 0) {
        input.value = (value - 1);
    }
});
document.getElementById('increment_topk').addEventListener('click', function () {
    var input = document.getElementById('vdb_topk');
    var value = parseFloat(input.value);
    if (value < 20) {
        input.value = (value + 1);
    }
});
document.getElementById('decrement_topn').addEventListener('click', function () {
    var input = document.getElementById('rank_topn');
    var value = parseFloat(input.value);
    if (value > 0) {
        input.value = (value - 1);
    }
});
document.getElementById('increment_topn').addEventListener('click', function () {
    var input = document.getElementById('rank_topn');
    var value = parseFloat(input.value);
    if (value < 10) {
        input.value = (value + 1);
    }
});
document.getElementById('decrement_sc').addEventListener('click', function () {
    var input = document.getElementById('input_score');
    var value = parseFloat(input.value);
    if (value > 0) {
        input.value = (value - 0.1).toFixed(1);
    }
});
document.getElementById('increment_sc').addEventListener('click', function () {
    var input = document.getElementById('input_score');
    var value = parseFloat(input.value);
    if (value < 1) {
        input.value = (value + 0.1).toFixed(1);
    }
});
document.getElementById('decrement_search').addEventListener('click', function () {
    var input = document.getElementById('search_range');
    var value = parseFloat(input.value);
    if (value > 0) {
        input.value = (value - 1);
    }
});
document.getElementById('increment_search').addEventListener('click', function () {
    var input = document.getElementById('search_range');
    var value = parseFloat(input.value);
    if (value < 3) {
        input.value = (value + 1);
    }
});