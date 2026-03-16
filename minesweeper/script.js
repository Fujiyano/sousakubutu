(function() {
    'use strict';

    const DIFFICULTIES = {
        easy:   { rows: 9,  cols: 9,  mines: 10 },
        medium: { rows: 16, cols: 16, mines: 40 },
        hard:   { rows: 16, cols: 30, mines: 99 }
    };

    let currentDifficulty = 'easy';
    let rows, cols, totalMines;
    let board = [];       // 2D array: each cell { mine, revealed, flagged, adjacentMines }
    let gameOver = false;
    let gameStarted = false;
    let firstClick = true;
    let flagCount = 0;
    let revealedCount = 0;
    let timerInterval = null;
    let seconds = 0;

    const boardEl = document.getElementById('board');
    const mineCounterEl = document.getElementById('mine-counter');
    const timerEl = document.getElementById('timer');
    const resetBtn = document.getElementById('reset-btn');
    const messageEl = document.getElementById('message');

    // Difficulty buttons
    document.querySelectorAll('.difficulty-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.difficulty-btn').forEach(function(b) {
                b.classList.remove('active');
            });
            btn.classList.add('active');
            currentDifficulty = btn.getAttribute('data-difficulty');
            initGame();
        });
    });

    resetBtn.addEventListener('click', function() {
        initGame();
    });

    function initGame() {
        var config = DIFFICULTIES[currentDifficulty];
        rows = config.rows;
        cols = config.cols;
        totalMines = config.mines;

        board = [];
        gameOver = false;
        gameStarted = false;
        firstClick = true;
        flagCount = 0;
        revealedCount = 0;
        seconds = 0;

        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }

        resetBtn.textContent = '🙂';
        messageEl.textContent = '';
        updateMineCounter();
        timerEl.textContent = '000';

        // Create board data
        for (var r = 0; r < rows; r++) {
            board[r] = [];
            for (var c = 0; c < cols; c++) {
                board[r][c] = {
                    mine: false,
                    revealed: false,
                    flagged: false,
                    adjacentMines: 0
                };
            }
        }

        renderBoard();
    }

    function placeMines(excludeRow, excludeCol) {
        var placed = 0;
        while (placed < totalMines) {
            var r = Math.floor(Math.random() * rows);
            var c = Math.floor(Math.random() * cols);
            // Exclude the first-click cell and its neighbors
            if (Math.abs(r - excludeRow) <= 1 && Math.abs(c - excludeCol) <= 1) {
                continue;
            }
            if (!board[r][c].mine) {
                board[r][c].mine = true;
                placed++;
            }
        }

        // Calculate adjacent mines
        for (var r = 0; r < rows; r++) {
            for (var c = 0; c < cols; c++) {
                if (!board[r][c].mine) {
                    board[r][c].adjacentMines = countAdjacentMines(r, c);
                }
            }
        }
    }

    function countAdjacentMines(row, col) {
        var count = 0;
        for (var dr = -1; dr <= 1; dr++) {
            for (var dc = -1; dc <= 1; dc++) {
                if (dr === 0 && dc === 0) continue;
                var nr = row + dr;
                var nc = col + dc;
                if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && board[nr][nc].mine) {
                    count++;
                }
            }
        }
        return count;
    }

    function renderBoard() {
        boardEl.innerHTML = '';
        boardEl.style.gridTemplateColumns = 'repeat(' + cols + ', 30px)';
        boardEl.style.gridTemplateRows = 'repeat(' + rows + ', 30px)';

        for (var r = 0; r < rows; r++) {
            for (var c = 0; c < cols; c++) {
                var cell = document.createElement('div');
                cell.className = 'cell';
                cell.setAttribute('data-row', r);
                cell.setAttribute('data-col', c);
                cell.addEventListener('click', onCellClick);
                cell.addEventListener('contextmenu', onCellRightClick);
                cell.addEventListener('mousedown', onCellMouseDown);
                cell.addEventListener('mouseup', onCellMouseUp);
                boardEl.appendChild(cell);
            }
        }
    }

    function getCellEl(row, col) {
        return boardEl.querySelector('[data-row="' + row + '"][data-col="' + col + '"]');
    }

    function onCellMouseDown(e) {
        if (gameOver) return;
        if (e.button === 0) {
            resetBtn.textContent = '😮';
        }
    }

    function onCellMouseUp() {
        if (gameOver) return;
        resetBtn.textContent = '🙂';
    }

    function onCellClick(e) {
        if (gameOver) return;

        var row = parseInt(e.currentTarget.getAttribute('data-row'));
        var col = parseInt(e.currentTarget.getAttribute('data-col'));
        var cellData = board[row][col];

        if (cellData.flagged || cellData.revealed) return;

        if (firstClick) {
            firstClick = false;
            placeMines(row, col);
            startTimer();
            gameStarted = true;
        }

        if (cellData.mine) {
            // Game over - hit a mine
            cellData.revealed = true;
            revealAllMines();
            gameOver = true;
            resetBtn.textContent = '😵';
            messageEl.textContent = 'ゲームオーバー！';
            stopTimer();

            var cellEl = getCellEl(row, col);
            cellEl.classList.add('revealed', 'mine-exploded');
            cellEl.textContent = '💣';
        } else {
            revealCell(row, col);
            checkWin();
        }
    }

    function onCellRightClick(e) {
        e.preventDefault();
        if (gameOver) return;

        var row = parseInt(e.currentTarget.getAttribute('data-row'));
        var col = parseInt(e.currentTarget.getAttribute('data-col'));
        var cellData = board[row][col];

        if (cellData.revealed) return;

        cellData.flagged = !cellData.flagged;
        var cellEl = getCellEl(row, col);

        if (cellData.flagged) {
            cellEl.textContent = '🚩';
            flagCount++;
        } else {
            cellEl.textContent = '';
            flagCount--;
        }

        updateMineCounter();
    }

    function revealCell(row, col) {
        if (row < 0 || row >= rows || col < 0 || col >= cols) return;

        var cellData = board[row][col];
        if (cellData.revealed || cellData.flagged || cellData.mine) return;

        cellData.revealed = true;
        revealedCount++;

        var cellEl = getCellEl(row, col);
        cellEl.classList.add('revealed');

        if (cellData.adjacentMines > 0) {
            cellEl.textContent = cellData.adjacentMines;
            cellEl.setAttribute('data-number', cellData.adjacentMines);
        } else {
            // Reveal neighbors for empty cells
            for (var dr = -1; dr <= 1; dr++) {
                for (var dc = -1; dc <= 1; dc++) {
                    if (dr === 0 && dc === 0) continue;
                    revealCell(row + dr, col + dc);
                }
            }
        }
    }

    function revealAllMines() {
        for (var r = 0; r < rows; r++) {
            for (var c = 0; c < cols; c++) {
                var cellData = board[r][c];
                var cellEl = getCellEl(r, c);
                if (cellData.mine && !cellData.revealed) {
                    cellEl.classList.add('revealed');
                    if (!cellData.flagged) {
                        cellEl.textContent = '💣';
                    }
                } else if (!cellData.mine && cellData.flagged) {
                    cellEl.classList.add('revealed');
                    cellEl.textContent = '❌';
                }
            }
        }
    }

    function checkWin() {
        var totalSafe = rows * cols - totalMines;
        if (revealedCount === totalSafe) {
            gameOver = true;
            resetBtn.textContent = '😎';
            messageEl.textContent = 'クリア！おめでとうございます！🎉';
            stopTimer();

            // Auto-flag remaining mines
            for (var r = 0; r < rows; r++) {
                for (var c = 0; c < cols; c++) {
                    if (board[r][c].mine && !board[r][c].flagged) {
                        board[r][c].flagged = true;
                        flagCount++;
                        var cellEl = getCellEl(r, c);
                        cellEl.textContent = '🚩';
                    }
                }
            }
            updateMineCounter();
        }
    }

    function updateMineCounter() {
        var remaining = totalMines - flagCount;
        var str = Math.abs(remaining).toString();
        while (str.length < 3) str = '0' + str;
        if (remaining < 0) str = '-' + str.slice(1);
        mineCounterEl.textContent = str;
    }

    function startTimer() {
        if (timerInterval) return;
        timerInterval = setInterval(function() {
            seconds++;
            if (seconds > 999) seconds = 999;
            var str = seconds.toString();
            while (str.length < 3) str = '0' + str;
            timerEl.textContent = str;
        }, 1000);
    }

    function stopTimer() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
    }

    // Initialize the game
    initGame();
})();
