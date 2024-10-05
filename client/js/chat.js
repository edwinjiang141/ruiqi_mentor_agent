const query = (obj) =>
  Object.keys(obj)
    .map((k) => encodeURIComponent(k) + "=" + encodeURIComponent(obj[k]))
    .join("&");
let file;
const colorThemes = document.querySelectorAll('[name="theme"]');
const markdown = window.markdownit({
  html: true // 允许 HTML
});

const message_box = document.getElementById(`messages`);
const message_input = document.getElementById(`message-input`);
const box_conversations = document.querySelector(`.top`);
const spinner = box_conversations.querySelector(".spinner");
const stop_generating = document.querySelector(`.stop_generating`);
const send_button = document.querySelector(`#send-button`);
let prompt_lock = false;

hljs.addPlugin(new CopyButtonPlugin());

function resizeTextarea(textarea) {
  textarea.style.height = '80px';
  textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

function refreshllm(inputmessage) {
  // 设置 message-input 元素的值
  const messageInput = document.getElementById('message-input');
  messageInput.value =  inputmessage;

  // 创建一个键盘事件来模拟按下回车键
  const enterEvent = new KeyboardEvent('keydown', {
    keyCode: 13,       // 回车键的 keyCode
    which: 13,         // 回车键的 keyCode
    key: 'Enter',      // 按键名称
    code: 'Enter',     // 按键代码
    bubbles: true,     // 事件可冒泡
    cancelable: true   // 事件可以被取消
  });

  // 在 message-input 元素上触发这个事件
  messageInput.dispatchEvent(enterEvent);
}

const format = (text) => {
  return text.replace(/(?:\r\n|\r|\n)/g, "<br>");
};

message_input.addEventListener("blur", () => {
  window.scrollTo(0, 0);
});

message_input.addEventListener("focus", () => {
  document.documentElement.scrollTop = document.documentElement.scrollHeight;
});

// 删除所有会话
const delete_conversations = async () => {
  localStorage.clear();
  await new_conversation();
};

// 处理用户输入
const handle_ask = async () => {
  message_input.style.height = `80px`;
  message_input.focus();

  window.scrollTo(0, 0);
  let message =  message_input.value;

  if (message.length > 0) {
    message_input.value = ``;
    await ask_gpt( message);
  }
};

// 移除取消按钮
const remove_cancel_button = async () => {
  stop_generating.classList.add(`stop_generating-hiding`);

  setTimeout(() => {
    stop_generating.classList.remove(`stop_generating-hiding`);
    stop_generating.classList.add(`stop_generating-hidden`);
  }, 300);
};

// 发送消息给GPT
const ask_gpt = async (message) => {
  try {
    message_input.value = ``;
    message_input.innerHTML = ``;
    message_input.innerText = ``;

    add_conversation(window.conversation_id, message.substr(0, 20));
    window.scrollTo(0, 0);
    window.controller = new AbortController();

    jailbreak = document.getElementById("jailbreak");
    model = document.getElementById("model");
    prompt_lock = true;
    window.text = ``;
    window.token = message_id();

    stop_generating.classList.remove(`stop_generating-hidden`);

    message_box.innerHTML += `
            <div class="message user-message" style="text-align: left">
             
                <div class="user">
                    ${user_image}
                    
                </div>
                <div class="content" id="user_${token}"> 
                    ${format(message)}
                </div>
            </div>
        `;

    message_box.scrollTop = message_box.scrollHeight;
    window.scrollTo(0, 0);
    await new Promise((r) => setTimeout(r, 500));
    window.scrollTo(0, 0);

    message_box.innerHTML += `
            <div class="message system-message">
                
                <div class="user">
                    ${gpt_image}  
                </div>
                <div class="content" id="gpt_${window.token}">
                    <div id="cursor"></div>
                    
                </div>
                
            </div>
            
        `;
        //<i id="refresh" class="fa fa-refresh icon-gray" aria-hidden="true" onclick="showmsg('user_${token}', '${format(message)}')"></i>

    message_box.scrollTop = message_box.scrollHeight;
    window.scrollTo(0, 0);
    await new Promise((r) => setTimeout(r, 1000));
    window.scrollTo(0, 0);

    // const response = await fetch(`/backend-api/v2/conversation`, {
    //   method: `POST`,
    //   signal: window.controller.signal,
    //   headers: {
    //     "content-type": `application/json`,
    //     accept: `text/event-stream`,
    //   },
    //   body: JSON.stringify({
    //     conversation_id: window.conversation_id,
    //     action: `_ask`,
    //     model: model.options[model.selectedIndex].value,
    //     jailbreak: jailbreak.options[jailbreak.selectedIndex].value,
    //     meta: {
    //       id: window.token,
    //       content: {
    //         conversation: await get_conversation(window.conversation_id),
    //         internet_access: document.getElementById("switch").checked,
    //         rag_access: document.getElementById("switch_rag").checked,
    //         temperature: document.getElementById("Temperature").value,
    //         content_type: "text",
    //         parts: [
    //           {
    //             content: message,
    //             role: "user",
    //           },
    //         ],
    //       },
    //     },
    //   }),
    // });

    const formData = new FormData();
    formData.append('conversation_id', window.conversation_id);
    formData.append('action', '_ask');
    formData.append('model', model.options[model.selectedIndex].value);
    formData.append('jailbreak', jailbreak.options[jailbreak.selectedIndex].value);

    // console.log("---------con id----------------------------------")

    // console.log(window.conversation_id)
    // console.log("-----------get_conversation--------------------------------")

    // console.log(get_conversation(window.conversation_id))
    // console.log("------------get_conversation end-------------------------------")

    const metaContent = {
      id: window.token,
      content: {
        conversation: await get_conversation(window.conversation_id),
        conversation_id: window.conversation_id,
        internet_access: document.getElementById("switch").checked,
        rag_access: document.getElementById("switch_rag").checked,
        temperature: document.getElementById("Temperature").value,
        vdb_topk: document.getElementById("vdb_topk").value,
        rank_topn: document.getElementById("rank_topn").value,
        rank_score: document.getElementById("input_score").value,
        search_range: document.getElementById("search_range").value,
        memory: document.getElementById("memory").value,
        languageSelect: document.getElementById("languageSelect").value,
        mentor_agent: document.getElementById("vectordb").value,
        cssgptinvoke:true,
        content_type: "text",
        parts: [
          {
            content:   message,
            role: "user",
          },
        ],
      },
    };

    formData.append('meta', JSON.stringify(metaContent));
    formData.append('upload_file', file);

    // console.log("-------------------------------------------")
    // console.log(window.controller.signal)
    // console.log("-------------------------------------------")
    // console.log(formData)

    // console.log("-------------------------------------------")

    const response = await fetch(`/backend-api/v2/conversation`, {
      method: `POST`,
      signal: window.controller.signal,
      // 不需要显式设置 content-type 头，浏览器会自动为 FormData 设置合适的内容类型
      headers: {
        accept: `text/event-stream`,
      },
      body: formData,
    });
    console.log(response)

    file = null;

    const reader = response.body.getReader();
    let text = ``;
    let isImage = false;
    let imageUrl = '';
    let chunks = '';

//     while (true) {
//       const { value, done } = await reader.read();
//       if (done) break;

//       let chunk = new TextDecoder().decode(value);
//       chunks += chunk;
//     }

//     console.log(chunks);

//     try {
//       const jsonChunks = JSON.parse(chunks);
//       if (jsonChunks.image_data && jsonChunks.image_data.startsWith('data:image')) {
//         isImage = true;
//         imageUrl = jsonChunks.image_data;
//       } else {
//         text += chunks;
//       }
//     } catch (e) {
//       text += chunks;
//     }

//     console.log("isImage: " + isImage);

//     if (isImage) {
//       document.getElementById(`gpt_${window.token}`).innerHTML = `<img src="${imageUrl}" alt="Generated Image" />`;
//     } else {
//       document.getElementById(`gpt_${window.token}`).innerHTML = markdown.render(text);
//       document.querySelectorAll(`code`).forEach((el) => {
//         hljs.highlightElement(el);
//       });
//     }

//     window.scrollTo(0, 0);
//     message_box.scrollTo({ top: message_box.scrollHeight, behavior: "auto" });

//     if (text.includes(`instead. Maintaining this website and API costs a lot of money`)) {
//       document.getElementById(`gpt_${window.token}`).innerHTML = "An error occured, please reload / refresh cache and try again.";
//     }

//     add_message(window.conversation_id, "user", message);
//     add_message(window.conversation_id, "assistant", text);

//     message_box.scrollTop = message_box.scrollHeight;
//     await remove_cancel_button();
//     prompt_lock = false;

//     await load_conversations(20, 0);
//     window.scrollTo(0, 0);
//   } catch (e) {
//     add_message(window.conversation_id, "user", message);

//     message_box.scrollTop = message_box.scrollHeight;
//     await remove_cancel_button();
//     prompt_lock = false;

//     await load_conversations(20, 0);

//     console.log(e);

//     let cursorDiv = document.getElementById(`cursor`);
//     if (cursorDiv) cursorDiv.parentNode.removeChild(cursorDiv);

//     if (e.name != `AbortError`) {
//       let error_message = `oops ! something went wrong, please try again / reload. [stacktrace in console]`;

//       document.getElementById(`gpt_${window.token}`).innerHTML = error_message;
//       add_message(window.conversation_id, "assistant", error_message);
//     } else {
//       document.getElementById(`gpt_${window.token}`).innerHTML += ` [aborted]`;
//       add_message(window.conversation_id, "assistant", text + ` [aborted]`);
//     }

//     window.scrollTo(0, 0);
//   }
// };

  let i = 1;
  

while (true) {
  const { value, done } = await reader.read();
  if (done) break;

    
  

  let chunk = new TextDecoder().decode(value);
  text += chunk;

  if (i == 1   ){
    if (chunk.includes('data:image')){
      isImage = true

    }
    console.log("isImage:" + isImage)

    

  } 
  if (!isImage){
    document.getElementById(`gpt_${window.token}`).innerHTML = markdown.render(text);
    document.querySelectorAll(`code`).forEach((el) => {
      hljs.highlightElement(el);
    });

    window.scrollTo(0, 0);
    message_box.scrollTo({ top: message_box.scrollHeight, behavior: "auto" });

  }
  i++

}

    

if (isImage) {
  const jsonChunks = JSON.parse(text);
  imageUrl = jsonChunks.image_data;
  
  document.getElementById(`gpt_${window.token}`).innerHTML = `<img src="${imageUrl}" alt="Generated Image"/>`;
  add_message(window.conversation_id, "user", message);
  add_message(window.conversation_id, "assistant", message);
    }else{
  if (text.includes(`instead. Maintaining this website and API costs a lot of money`)) {
    document.getElementById(`gpt_${window.token}`).innerHTML = "An error occured, please reload / refresh cache and try again.";
  }
  add_message(window.conversation_id, "user", message);
  add_message(window.conversation_id, "assistant", text);

    }





message_box.scrollTop = message_box.scrollHeight;
await remove_cancel_button();
prompt_lock = false;

await load_conversations(20, 0);
window.scrollTo(0, 0);
  } catch (e) {
  add_message(window.conversation_id, "user", message);

  message_box.scrollTop = message_box.scrollHeight;
  await remove_cancel_button();
  prompt_lock = false;

  await load_conversations(20, 0);

  console.log(e);

  let cursorDiv = document.getElementById(`cursor`);
  if (cursorDiv) cursorDiv.parentNode.removeChild(cursorDiv);

  if (e.name != `AbortError`) {
    let error_message = `oops ! something went wrong, please try again / reload. [stacktrace in console]`;

    document.getElementById(`gpt_${window.token}`).innerHTML = error_message;
    add_message(window.conversation_id, "assistant", error_message);
  } else {
    document.getElementById(`gpt_${window.token}`).innerHTML += ` [aborted]`;
    add_message(window.conversation_id, "assistant", text + ` [aborted]`);
  }

  window.scrollTo(0, 0);
}
};






// 清空会话列表
const clear_conversations = async () => {
  const elements = box_conversations.childNodes;
  let index = elements.length;

  if (index > 0) {
    while (index--) {
      const element = elements[index];
      if (element.nodeType === Node.ELEMENT_NODE && element.tagName.toLowerCase() !== `button`) {
        box_conversations.removeChild(element);
      }
    }
  }
};

// 清空当前会话
const clear_conversation = async () => {
  let messages = message_box.getElementsByTagName(`div`);

  while (messages.length > 0) {
    message_box.removeChild(messages[0]);
  }
};

// 显示删除选项
const show_option = async (conversation_id) => {
  const conv = document.getElementById(`conv-${conversation_id}`);
  const yes = document.getElementById(`yes-${conversation_id}`);
  const not = document.getElementById(`not-${conversation_id}`);

  conv.style.display = "none";
  yes.style.display = "block";
  not.style.display = "block";
}

// 隐藏删除选项
const hide_option = async (conversation_id) => {
  const conv = document.getElementById(`conv-${conversation_id}`);
  const yes = document.getElementById(`yes-${conversation_id}`);
  const not = document.getElementById(`not-${conversation_id}`);

  conv.style.display = "block";
  yes.style.display = "none";
  not.style.display = "none";
}

// 删除会话
const delete_conversation = async (conversation_id) => {
  localStorage.removeItem(`conversation:${conversation_id}`);

  const conversation = document.getElementById(`convo-${conversation_id}`);
  conversation.remove();

  if (window.conversation_id == conversation_id) {
    await new_conversation();
  }

  await load_conversations(20, 0, true);
};

// 设置当前会话
const set_conversation = async (conversation_id) => {
  welcomeMessage = document.getElementById('welcome-message');
  welcomeMessage.style.display = 'none';
  history.pushState({}, null, `/chat/${conversation_id}`);
  window.conversation_id = conversation_id;

  await clear_conversation();
  await load_conversation(conversation_id);
  await load_conversations(20, 0, true);
};

// 创建新会话
const new_conversation = async () => {
  history.pushState({}, null, `/chat/`);
  window.conversation_id = uuid();

  await clear_conversation();
  await load_conversations(20, 0, true);
};

// 加载会话内容
const load_conversation = async (conversation_id) => {
  let conversation = await JSON.parse(localStorage.getItem(`conversation:${conversation_id}`));
  console.log(conversation, conversation_id);

  for (item of conversation.items) {
    message_box.innerHTML += `
            <div class="message">
                <div class="user ">
                    ${item.role == "assistant" ? gpt_image : user_image}
                   
                </div>
                <div class="content">
                    ${item.role == "assistant" ? markdown.render(item.content) : item.content}
                </div>
            </div>
        `;
  }

  document.querySelectorAll(`code`).forEach((el) => {
    hljs.highlightElement(el);
  });

  message_box.scrollTo({ top: message_box.scrollHeight, behavior: "smooth" });

  setTimeout(() => {
    message_box.scrollTop = message_box.scrollHeight;
  }, 500);
};

// 获取会话内容
const get_conversation = async (conversation_id) => {
  let conversation = await JSON.parse(localStorage.getItem(`conversation:${conversation_id}`));
  return conversation.items;
};

//导出会话内容

const export_conversation = async (conversation_id) => {
  let conversation = await JSON.parse(localStorage.getItem(`conversation:${conversation_id}`));
  let chatLog = [];

  for (item of conversation.items) {
    chatLog.push(`
            <div class="message">
                <div class="user ">
                    ${item.role == "assistant" ? 'Mentor:':'User Question:'}
                   
                </div>
                <div class="content">
                    ${item.role == "assistant" ? markdown.render(item.content) : item.content}
                </div>
            </div>
        `);
  }
  
  let htmlContent = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chat Log</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .message { margin-bottom: 10px; }
            .user { color: blue; }
            .ai { color: green; }
        </style>
    </head>
    <body>
        <h1>初中物化导师平台记录</h1>
        ${chatLog}
    </body>
    </html>
    `;

    // 创建一个Blob对象
  const blob = new Blob([htmlContent], { type: 'text/plain' });

  // 创建一个下载链接
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = 'chat_'+conversation_id+'_log.html';

  // 触发下载
  document.body.appendChild(a);
  a.click();

  // 移除下载链接
  window.URL.revokeObjectURL(url);
  a.remove();

  // chatstrt = conversation.items
  // const chatData = encodeURIComponent(JSON.stringify(chatstr));
  // const shareableLink = `${window.location.href}?chat=${chatData}`;
  // console.log(shareableLink);
  // return shareableLink;
};

// 添加会话
const add_conversation = async (conversation_id, title) => {
  if (localStorage.getItem(`conversation:${conversation_id}`) == null) {
    localStorage.setItem(
      `conversation:${conversation_id}`,
      JSON.stringify({
        id: conversation_id,
        title: title,
        items: [],
      })
    );
  }
};

// 添加消息
const MAX_STORAGE_SIZE = 64 * 1024 * 1024; // 5MB

const add_message = async (conversation_id, role, content) => {
  let conversation = JSON.parse(localStorage.getItem(`conversation:${conversation_id}`));
  if (!conversation) {
    conversation = {
      id: conversation_id,
      items: [],
    };
  }

  conversation.items.push({
    role: role,
    content: content,
  });

  try {
    localStorage.setItem(`conversation:${conversation_id}`, JSON.stringify(conversation));
  } catch (e) {
    if (e.name === 'QuotaExceededError' || e.name === 'NS_ERROR_DOM_QUOTA_REACHED') {
      // 清理旧消息以腾出空间
      while (conversation.items.length > 0 && JSON.stringify(localStorage).length >= MAX_STORAGE_SIZE) {
        conversation.items.shift(); // 移除最旧的消息
        try {
          localStorage.setItem(`conversation:${conversation_id}`, JSON.stringify(conversation));
        } catch (e) {
          if (e.name === 'QuotaExceededError' || e.name === 'NS_ERROR_DOM_QUOTA_REACHED') {
            continue;
          }
          throw e;
        }
      }
    } else {
      throw e;
    }
  }
};


// 加载会话列表
const load_conversations = async (limit, offset, loader) => {
  let conversations = [];
  for (let i = 0; i < localStorage.length; i++) {
    if (localStorage.key(i).startsWith("conversation:")) {
      let conversation = localStorage.getItem(localStorage.key(i));
      conversations.push(JSON.parse(conversation));
    }
  }

  await clear_conversations();

  for (conversation of conversations) {
    box_conversations.innerHTML += `
    <div class="convo" id="convo-${conversation.id}">
      <div class="left" onclick="set_conversation('${conversation.id}')">
          <i class="fa-regular fa-comments"></i>
          <span class="convo-title">${conversation.title}</span>
      </div>
      <i onclick="show_option('${conversation.id}')" class="fa-regular fa-trash" id="conv-${conversation.id}"></i>
      <i onclick="delete_conversation('${conversation.id}')" class="fa-regular fa-check" id="yes-${conversation.id}" style="display:none;"></i>
      <i onclick="hide_option('${conversation.id}')" class="fa-regular fa-x" id="not-${conversation.id}" style="display:none;"></i>

      <i onclick="export_conversation('${conversation.id}')" id="conv-${conversation.id}" title="Export Chat Log">📚</i>

    </div>
    `;
  }

  document.querySelectorAll(`code`).forEach((el) => {
    hljs.highlightElement(el);
  });
};

// 监听取消按钮点击事件
document.getElementById(`cancelButton`).addEventListener(`click`, async () => {
  window.controller.abort();
  console.log(`aborted ${window.conversation_id}`);
});

function h2a(str1) {
  var hex = str1.toString();
  var str = "";

  for (var n = 0; n < hex.length; n += 2) {
    str += String.fromCharCode(parseInt(hex.substr(n, 2), 16));
  }

  return str;
}

// 生成UUID
const uuid = () => {
  return `xxxxxxxx-xxxx-4xxx-yxxx-${Date.now().toString(16)}`.replace(
    /[xy]/g,
    function (c) {
      var r = (Math.random() * 16) | 0,
        v = c == "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    }
  );
};

// 生成消息ID
const message_id = () => {
  random_bytes = (Math.floor(Math.random() * 1338377565) + 2956589730).toString(
    2
  );
  unix = Math.floor(Date.now() / 1000).toString(2);

  return BigInt(`0b${unix}${random_bytes}`).toString();
};

window.onload = async () => {
  load_settings_localstorage();

  conversations = 0;
  for (let i = 0; i < localStorage.length; i++) {
    if (localStorage.key(i).startsWith("conversation:")) {
      conversations += 1;
    }
  }

  if (conversations == 0) localStorage.clear();

  await setTimeout(() => {
    load_conversations(20, 0);
  }, 1);

  if (!window.location.href.endsWith(`#`)) {
    if (/\/chat\/.+/.test(window.location.href)) {
      await load_conversation(window.conversation_id);
    }
  }

  message_input.addEventListener(`keydown`, async (evt) => {
    if (prompt_lock) return;
    if (evt.keyCode === 13 && !evt.shiftKey) {
      evt.preventDefault();
      console.log('pressed enter');
      await handle_ask();
    } else {
      message_input.style.removeProperty("height");
      message_input.style.height = message_input.scrollHeight + 4 + "px";
    }
  });

  send_button.addEventListener(`click`, async () => {
    console.log("clicked send");
    if (prompt_lock) return;
    await handle_ask();
  });

  register_settings_localstorage();
};

document.querySelector(".mobile-sidebar").addEventListener("click", (event) => {
  const sidebar = document.querySelector(".conversations");

  if (sidebar.classList.contains("shown")) {
    sidebar.classList.remove("shown");
    event.target.classList.remove("rotated");
  } else {
    sidebar.classList.add("shown");
    event.target.classList.add("rotated");
  }

  window.scrollTo(0, 0);
});

// 注册设置到localStorage
const register_settings_localstorage = async () => {
  settings_ids = ["switch", "model", "jailbreak","languageSelect"];
  settings_elements = settings_ids.map((id) => document.getElementById(id));
  settings_elements.map((element) =>
    element.addEventListener(`change`, async (event) => {
      switch (event.target.type) {
        case "checkbox":
          localStorage.setItem(event.target.id, event.target.checked);
          break;
        case "select-one":
          localStorage.setItem(event.target.id, event.target.selectedIndex);
          break;
        default:
          console.warn("Unresolved element type");
      }
    })
  );
};

// 从localStorage加载设置
const load_settings_localstorage = async () => {
  settings_ids = ["switch", "model", "jailbreak", "languageSelect"];
  settings_elements = settings_ids.map((id) => document.getElementById(id));
  settings_elements.map((element) => {
    if (localStorage.getItem(element.id)) {
      switch (element.type) {
        case "checkbox":
          element.checked = localStorage.getItem(element.id) === "true";
          break;
        case "select-one":
          element.selectedIndex = parseInt(localStorage.getItem(element.id));
          break;
        default:
          console.warn("Unresolved element type");
      }
    }
  });
};

// 主题存储
const storeTheme = function (theme) {
  localStorage.setItem("theme", theme);
};

// 设置主题
const setTheme = function () {
  const activeTheme = localStorage.getItem("theme");
  colorThemes.forEach((themeOption) => {
    if (themeOption.id === activeTheme) {
      themeOption.checked = true;
    }
  });
  // fallback for no :has() support
  document.documentElement.className = activeTheme;
};

colorThemes.forEach((themeOption) => {
  themeOption.addEventListener("click", () => {
    storeTheme(themeOption.id);
    // fallback for no :has() support
    document.documentElement.className = themeOption.id;
  });
});

document.onload = setTheme();
