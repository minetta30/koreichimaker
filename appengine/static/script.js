document.addEventListener('DOMContentLoaded', function() {
    const inputForm = document.getElementById('inputForm');
    const suggestionBox = document.getElementById('suggestionBox');

    // サジェストしたい値のリスト
    let suggestions = [];

    // サーバーからサジェストリストを取得
    fetch('/api/suggestions')
        .then(response => response.json())
        .then(data => {
            suggestions = data;
        })
        .catch(error => console.error('Error:', error));

    console.log(suggestions);

    inputForm.addEventListener('input', function() {
        const inputText = inputForm.value.toLowerCase();
        suggestionBox.innerHTML = ''; // サジェストボックスをクリア

        if (!inputText) {
            return; // 入力が空の場合は何も表示しない
        }

        // 入力値に一致する要素を検索し、サジェストボックスに表示
        suggestions.filter(item => item.toLowerCase().includes(inputText))
                   .forEach(suggestion => {
                       const div = document.createElement('div');
                       div.textContent = suggestion;
                       div.addEventListener('click', () => {
                           inputForm.value = suggestion; // 選択した値を入力フォームにセット
                           suggestionBox.innerHTML = ''; // サジェストボックスをクリア
                       });
                       suggestionBox.appendChild(div);
                   });
    });
});