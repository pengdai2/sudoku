<?php
putenv("PATH=/Users/ped/sudoku:$PATH");
$sudoku = $_GET["sudoku"];
passthru("post.py $sudoku");
?>
