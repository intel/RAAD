Time Series
###########
Tutorial
    - https://www.cs.ucr.edu/~eamonn/tutorials.html

List of Rapid Learning based on Publications
*********************************************
    - List of Publications and Links
        - Searching and Mining Trillions of Time Series Subsequences under Dynamic Time Warping SIGKDD 2012. Thanawin Rakthanmanon, Bilson Campana, Abdullah Mueen, Gustavo Batista, Brandon Westover, Qiang Zhu, Jesin Zakaria, Eamonn Keogh (2012). Best paper award [pdf].[data/code/video]
            - http://www.cs.ucr.edu/~eamonn/SIGKDD_trillion.pdf
            - http://www.cs.ucr.edu/~eamonn/UCRsuite.html
        - Instruction Set Extensions for Dynamic Time Warping. J. Tarango, E. Keogh, and P. Brisk. International Conference on Hardware/Software Codesign and System Synthesis (CODES-ISSS) Montreal, Canada, September 29 -October 4, 2013. [Paper] [Slides] [Poster]
            - https://www.cs.ucr.edu/~jtarango/docs/codes13-edtw.pdf
            - https://www.cs.ucr.edu/~jtarango/docs/codes13-edtw.pptx
            - https://www.cs.ucr.edu/~jtarango/docs/grd.pdf
        - Matrix Profile I: All Pairs Similarity Joins for Time Series: A Unifying View that Includes Motifs, Discords and Shapelets. Chin-Chia Michael Yeh, Yan Zhu, Liudmila Ulanova, Nurjahan Begum, Yifei Ding, Hoang Anh Dau, Diego Furtado Silva, Abdullah Mueen, Eamonn Keogh (2016). IEEE ICDM 2016. [pdf] [slides]
            - https://www.cs.ucr.edu/~eamonn/PID4481997_extend_Matrix%20Profile_I.pdf
            - https://www.cs.ucr.edu/~eamonn/matrix_profile_i.pptx

Videos
******
    - From Data to Knowledge - 102 by Dr. Keogh
        - https://youtu.be/v5F-lK8GOYY
    - Shaplets, Motifs and Discords: A set of Primitives for Mining Massive Time Series and Image Archives by Dr. Keogh
        - https://youtu.be/sD-vvN_st58
    - SAXually Explicit Images: Data Mining Large Shape Databases by Dr. Keogh
        - https://youtu.be/vzPgHF7gcUQ
    - Searching and mining trillions of time series subsequences under dynamic time warping (KDD 2012) by Dr. Rakthanmanon
        - https://youtu.be/xI26fQPbdX8
    - UCRSuite: Fast Subsequence Search (DNA)
        - https://youtu.be/c7xz9pVr05Q
    - UCR Suite: Fast Nearest Neighbor Search (Top-1 NN)
        - https://youtu.be/d_qLzMMuVQg
    - Data Mining Profiling Part 1 background by Dr. Keogh
        - https://www.youtube.com/watch?v=1ZHW977t070
    - Data Mining Profiling Part 2 algorithms by Dr. Mudeen
        - https://www.youtube.com/watch?v=LnQneYvg84M
    - Real time Motif Discovery on Parallel Accelerators by Dr. Zach Zimmerman
        - https://youtu.be/fDmeCzpp96s

Researchers
***********
    - Eamonn Keogh, Professor at University of California, Riverside.
    - Abdullah Mudeen, Professor at University of New Mexico .
    - Zach Zimmerman, Research Scientist at Google focusing on search.
    - Philip Brisk, Professor at University of California, Riverside.
    - Joseph Tarango, Adjunct Professor University of Colorado, Boulder.

Research Direction
******************
    - Problem statement
        - Time series data in the real world is multifaceted in nature and ordered. Algorithms in the past approximately matched queries, focused the solution on one data set, vary in computational cost, and storage space.
    - Solution approach
        - Time series data in the real world are typically conserved in repeated patterns.
        - Searching through large sets of data we want to ensure all features are conserved.
        - Any measures should have high accuracy.
        - The methods should be simple and parameter free to prevent over-fitting.
        - The dimensionality of the query on a timeseries should be on the same order, meaning we want to maintain O(N) or linear time.
        - Ensure missing data does not cause false positives.
        - The algorithm should be agnostic to the data set.
    - Other state-of-the-art solutions
        - Spatial tuning through hashing, focused on one specific usage.
        - Similar algorithms increase in runtime polynomial as the query grows.
