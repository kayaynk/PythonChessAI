"""
Satranç oyununun mevcut durumu ile ilgili tüm bilgileri saklamak.
Mevcut durumda geçerli hamlelerin belirlenmesi.
Hareket kaydını tutacaktır.
"""


class GameState:
    def __init__(self):
        """
        Pano 8x8 2d bir listedir, listedeki her eleman 2 karakterden oluşur.
        İlk karakter, parçanın rengini temsil eder: "b" veya "w".
        İkinci karakter parçanın türünü temsil eder: 'R', 'N', 'B', 'Q', 'K' veya 'p'.
        "--" parçası olmayan boş bir alanı temsil eder.
        """
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFunctions = {"p": self.getPawnMoves, "R": self.getRookMoves, "N": self.getKnightMoves,
                              "B": self.getBishopMoves, "Q": self.getQueenMoves, "K": self.getKingMoves}
        self.white_to_move = True
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.in_check = False
        self.pins = []
        self.checks = []
        self.enpassant_possible = ()  # geçerken yemenin mümkün olduğu karenin koordinatları
        self.enpassant_possible_log = [self.enpassant_possible]
        self.current_castling_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                               self.current_castling_rights.wqs, self.current_castling_rights.bqs)]

    def makeMove(self, move):
        """
         Bir Taşı'yı parametre olarak alır ve yürütür.
        (bu rok atma, piyon terfi ve geçerken alma için işe yaramaz)
        """
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)  # hareketi move'a kaydet, böylece daha sonra geri alabiliriz
        self.white_to_move = not self.white_to_move  # oyuncuları değiştir
        # taşındıysa kralın yerini güncelle
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        # piyon terfisi
        if move.is_pawn_promotion:
            # if not is_AI:
            #    promoted_piece = input("Promote to Q, R, B, or N:") #bunu daha sonra kullanıcı arayüzüne götür
            #    self.board[move.end_row][move.end_col] = move.piece_moved[0] + promoted_piece
            # else:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q"

        # geçiş haraketi
        if move.is_enpassant_move:
            self.board[move.start_row][move.end_col] = "--"

        # enpassant_possible parametresini güncelle
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:  # sadece 2 kare piyon avansında
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.enpassant_possible = ()

        # rok
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # şah kanadına rok
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][
                    move.end_col + 1]  # kaleyi yeni konumuna taşır
                self.board[move.end_row][move.end_col + 1] = '--'  # eski kaleyi sil
            else:  # vezir kanadına rok
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][
                    move.end_col - 2]  # kaleyi yeni konumuna taşır
                self.board[move.end_row][move.end_col - 2] = '--'  # eski kaleyi sil

        self.enpassant_possible_log.append(self.enpassant_possible)

        # rok haklarını güncelle; kale veya şah hamlesi olduğunda
        self.updateCastleRights(move)
        self.castle_rights_log.append(CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                                   self.current_castling_rights.wqs, self.current_castling_rights.bqs))

    def undoMove(self):
        """
        Son hamleyi geri al
        """
        if len(self.move_log) != 0:  # geri alınacak bir hareket olduğundan emin olun
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move  #oyuncuları değiştir
            # gerekirse şahın konumunu güncelleyin
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)
            # geçen hamleleri geri almak
            if move.is_enpassant_move:
                self.board[move.end_row][move.end_col] = "--"  # rok alanını boş bırakın
                self.board[move.start_row][move.end_col] = move.piece_captured

            self.enpassant_possible_log.pop()
            self.enpassant_possible = self.enpassant_possible_log[-1]

            # rok haklarını geri al
            self.castle_rights_log.pop()  # Geri aldığımız hamleden yeni rok haklarından kurtulun
            self.current_castling_rights = self.castle_rights_log[
                -1]  # mevcut rok haklarını listedeki sonuncuya ayarla
            # rok hareketini geri al
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:  # şah kanadı
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = '--'
                else:  # vezir kanadı
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = '--'
            self.checkmate = False
            self.stalemate = False

    def updateCastleRights(self, move):
        """
        oynanan rok haklarını güncelle
        """
        if move.piece_captured == "wR":
            if move.end_col == 0:  # sol kale
                self.current_castling_rights.wqs = False
            elif move.end_col == 7:  # sağ kale
                self.current_castling_rights.wks = False
        elif move.piece_captured == "bR":
            if move.end_col == 0:  # sol kale
                self.current_castling_rights.bqs = False
            elif move.end_col == 7:  # sağ kale
                self.current_castling_rights.bks = False

        if move.piece_moved == 'wK':
            self.current_castling_rights.wqs = False
            self.current_castling_rights.wks = False
        elif move.piece_moved == 'bK':
            self.current_castling_rights.bqs = False
            self.current_castling_rights.bks = False
        elif move.piece_moved == 'wR':
            if move.start_row == 7:
                if move.start_col == 0:  # sol kale
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7:  # sağ kale
                    self.current_castling_rights.wks = False
        elif move.piece_moved == 'bR':
            if move.start_row == 0:
                if move.start_col == 0:  # sol kale
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7:  # sağ kale
                    self.current_castling_rights.bks = False

    def getValidMoves(self):
        """
        Şahlar dikkate alınarak tüm haraketler
        """
        temp_castle_rights = CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                          self.current_castling_rights.wqs, self.current_castling_rights.bqs)
        # gelişmiş algoritma
        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()

        if self.white_to_move:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]
        if self.in_check:
            if len(self.checks) == 1:  # sadece 1 şah, şahı engelle veya Şahı(kralı) hareket ettir
                moves = self.getAllPossibleMoves()
                # şahı bloke etmek için, düşman taşı ile şahınız(kralınızın) arasındaki karelerden birine bir taş koymalısınız.
                check = self.checks[0]  # Şahları kontrol et
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col] # şaha neden olan düşman taşı
                valid_squares = []  # Taşların taşınabileceği kareler
                # At varsa, atı ele geçirmeliyiz veya şahı hareket ettirmeliyiz, diğer taşlar engellenebilir
                if piece_checking[1] == "N":
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i,
                                        king_col + check[3] * i)  #2li ve 3lü şah kontrolu
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[
                            1] == check_col:  # taşları ve şahları kontrol ettikten sonra
                            break
                # kontrolü engelleyen veya şahı hareket ettirmeyen tüm hamlelerden kurtulun
                for i in range(len(moves) - 1, -1, -1):  # öğeleri kaldırırken listeyi geriye doğru yineleyin
                    if moves[i].piece_moved[1] != "K":  # Şahı hareket ettiremiyoruz, bu yüzden şah engellenmeli veya ele geçirilmesi gerekir
                        if not (moves[i].end_row,
                                moves[i].end_col) in valid_squares:  # Harkaetimiz taşı engellemez veya ele geçiremez
                            moves.remove(moves[i])
            else:  # çifte şah , kral hareket etmeli
                self.getKingMoves(king_row, king_col, moves)
        else:  # şah yok tüm haraketler yapılabilir
            moves = self.getAllPossibleMoves()
            if self.white_to_move:
                self.getCastleMoves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.getCastleMoves(self.black_king_location[0], self.black_king_location[1], moves)

        if len(moves) == 0:
            if self.inCheck():
                self.checkmate = True
            else:
                # TODO stalemate on repeated moves
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.current_castling_rights = temp_castle_rights
        return moves

    def inCheck(self):
        """
        Mevcut bir taşın şah açmazında olup olmadığını kontrol edin
        """
        if self.white_to_move:
            return self.squareUnderAttack(self.white_king_location[0], self.white_king_location[1])
        else:
            return self.squareUnderAttack(self.black_king_location[0], self.black_king_location[1])

    def squareUnderAttack(self, row, col):
        """
        Düşmanın r, c karesine saldırıp saldıramayacağını belirleyin
        """
        self.white_to_move = not self.white_to_move  # rakibin bakış açısına geç
        opponents_moves = self.getAllPossibleMoves()
        self.white_to_move = not self.white_to_move
        for move in opponents_moves:
            if move.end_row == row and move.end_col == col:  #kare saldırı altında
                return True
        return False

    def getAllPossibleMoves(self):
        """
        Şahlar dikkate almadan tüm hareketler.
        """
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                turn = self.board[row][col][0]
                if (turn == "w" and self.white_to_move) or (turn == "b" and not self.white_to_move):
                    piece = self.board[row][col][1]
                    self.moveFunctions[piece](row, col, moves)  # Taş türüne göre uygun hareket fonksiyonunu çağırır
        return moves

    def checkForPinsAndChecks(self):
        pins = []  # Tutulmuş kalaler
        checks = []  # düşmanın şah uyguladığı kareler
        in_check = False
        if self.white_to_move:
            enemy_color = "b"
            ally_color = "w"
            start_row = self.white_king_location[0]
            start_col = self.white_king_location[1]
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row = self.black_king_location[0]
            start_col = self.black_king_location[1]
        # Şahın(kralın) haraket edebileceği karaler
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            direction = directions[j]
            possible_pin = ()  # tutulan karaleri sıfırla
            for i in range(1, 8):
                end_row = start_row + direction[0] * i
                end_col = start_col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != "K":
                        if possible_pin == ():  # 1. dost taş koyulabilir
                            possible_pin = (end_row, end_col, direction[0], direction[1])
                        else:  # 2. dost taş  bu yönde şah veya tutulan kale yok
                            break
                    elif end_piece[0] == enemy_color:
                        enemy_type = end_piece[1]
                        # Bu karmaşık koşulda 5 olasılık
                        # 1.) kraldan ortogonal olarak uzakta ve taş bir kaledir
                        # 2) kraldan çapraz olarak uzakta ve taş bir fildir
                        # 3.) Şahtan çapraz olarak 1 kare uzakta ve taş bir piyon
                        # 4) Herhangi bir yön ve parça bir vezirdir
                        # 5.) 1 kare uzaklıkta herhangi bir yön ve taş kraldır
                        if (0 <= j <= 3 and enemy_type == "R") or (4 <= j <= 7 and enemy_type == "B") or (
                                i == 1 and enemy_type == "p" and (
                                (enemy_color == "w" and 6 <= j <= 7) or (enemy_color == "b" and 4 <= j <= 5))) or (
                                enemy_type == "Q") or (i == 1 and enemy_type == "K"):
                            if possible_pin == ():  # parça engellemesi yok, bu yüzden şah
                                in_check = True
                                checks.append((end_row, end_col, direction[0], direction[1]))
                                break
                            else:  # taş engelliyor bu yüzden şah yok
                                pins.append(possible_pin)
                                break
                        else:  # düşman taşı var bu yüzden şah yok
                            break
                else:
                    break
        # At şahlarının kontrolü
        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "N":  # Şaha saldıran düşman at
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))
        return in_check, pins, checks

    def getPawnMoves(self, row, col, moves):
        """
        Satırda, sütunda bulunan piyon için tüm piyon hareketlerini alın ve move'a hamleleri ekleyin.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.white_to_move:
            move_amount = -1
            start_row = 6
            enemy_color = "b"
            king_row, king_col = self.white_king_location
        else:
            move_amount = 1
            start_row = 1
            enemy_color = "w"
            king_row, king_col = self.black_king_location

        if self.board[row + move_amount][col] == "--":  # 1 kare piyon ilerlemesi
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Move((row, col), (row + move_amount, col), self.board))
                if row == start_row and self.board[row + 2 * move_amount][col] == "--":  # 2 kare piyon ilerlemesi
                    moves.append(Move((row, col), (row + 2 * move_amount, col), self.board))
        if col - 1 >= 0:  # sola taş yeme
            if not piece_pinned or pin_direction == (move_amount, -1):
                if self.board[row + move_amount][col - 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col - 1), self.board))
                if (row + move_amount, col - 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  # şah piyonun solunda
                            # içeride: şah ve piyon arasında;
                            # dış: piyon ve sınır arasında;
                            inside_range = range(king_col + 1, col - 1)
                            outside_range = range(col + 1, 8)
                        else:  # şah piyonun sağında
                            inside_range = range(king_col - 1, col, -1)
                            outside_range = range(col - 2, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":  # bazı taşlar piyonları engelliyor
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col - 1), self.board, is_enpassant_move=True))
        if col + 1 <= 7:  # sağa yakalama
            if not piece_pinned or pin_direction == (move_amount, +1):
                if self.board[row + move_amount][col + 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col + 1), self.board))
                if (row + move_amount, col + 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  # şah piyonun solunda
                            # içeride: şah ve piyon arasında;
                            # dış: piyon ve sınır arasında;
                            inside_range = range(king_col + 1, col)
                            outside_range = range(col + 2, 8)
                        else:  # şah piyonun sağında
                            inside_range = range(king_col - 1, col + 1, -1)
                            outside_range = range(col - 1, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":  # bazı taşlar piyonları engelliyor
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col + 1), self.board, is_enpassant_move=True))

    def getRookMoves(self, row, col, moves):
        """
        Satırda, sütunda bulunan kale için tüm kale hareketlerini alın ve move'a hamleleri ekleyin.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[row][col][
                    1] != "Q":
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))  # yukarı, sol, aşağı, sağ
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  # haraketlerin tahtada olup olmadığını kontrol edin
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # boş alan geçerlidir
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # düşman taşını ele geçirmek
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  # dost taş
                            break
                else:
                    break

    def getKnightMoves(self, row, col, moves):
        """
        Satırda, sütunda bulunan at için tüm at hareketlerini alın ve move'a hamleleri ekleyin.
        """
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2),
                        (1, -2))  # yukarı / sol yukarı / sağ sağ / yukarı sağ / aşağı aşağı / sol aşağı / sağ sol / yukarı sola / aşağı
        ally_color = "w" if self.white_to_move else "b"
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:  # ya düşman taşı ya da boş kare
                        moves.append(Move((row, col), (end_row, end_col), self.board))

    def getBishopMoves(self, row, col, moves):
        """
         Satırda, sütunda bulunan fil için tüm fil hareketlerini alın ve move'a hamleleri ekleyin.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, 1), (1, -1))  # köşegenler: yukarı / sol yukarı / sağ aşağı / sağ aşağı / sol
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  # haraketlerin tahtada lup olmadığını kontrol edin
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--": #boş alan geçerlidir
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # düşman taşını ele geçirmek
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  # dost taş
                            break
                else:
                    break

    def getQueenMoves(self, row, col, moves):
        """
        Satırda ve sütünda bulunan vezir için tüm vezir hareketlerini alın ve move'a ekleyin.
        """
        self.getBishopMoves(row, col, moves)
        self.getRookMoves(row, col, moves)

    def getKingMoves(self, row, col, moves):
        """
        Satırda ve sütünda bulunan şah için tüm şah hareketlerini alın ve move'a ekleyin.
        """
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = "w" if self.white_to_move else "b"
        for i in range(8):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:  # bir dost taş değil - boş veya düşman
                    # Şahı(kralı) bitiş karesine yerleştirin ve şahları kontrol edin
                    if ally_color == "w":
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    in_check, pins, checks = self.checkForPinsAndChecks()
                    if not in_check:
                        moves.append(Move((row, col), (end_row, end_col), self.board))
                    # Şahı orijinal konumuna geri yerleştir
                    if ally_color == "w":
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

    def getCastleMoves(self, row, col, moves):
        """
        (Row, col) konumunda şah için geçerli tüm kale hareketlerini oluşturun ve bunları move listesine ekleyin.
        """
        if self.squareUnderAttack(row, col):
            return  # şah çekilmişken rok yapılamaz
        if (self.white_to_move and self.current_castling_rights.wks) or (
                not self.white_to_move and self.current_castling_rights.bks):
            self.getKingsideCastleMoves(row, col, moves)
        if (self.white_to_move and self.current_castling_rights.wqs) or (
                not self.white_to_move and self.current_castling_rights.bqs):
            self.getQueensideCastleMoves(row, col, moves)

    def getKingsideCastleMoves(self, row, col, moves):
        if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':
            if not self.squareUnderAttack(row, col + 1) and not self.squareUnderAttack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, is_castle_move=True))

    def getQueensideCastleMoves(self, row, col, moves):
        if self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--':
            if not self.squareUnderAttack(row, col - 1) and not self.squareUnderAttack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, is_castle_move=True))


class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move:
    # satrançta, tahtadaki alanlar, biri 1-8 arası sayı olan (satırlara karşılık gelen) iki sembolle tanımlanır
    # ve ikincisi a-f arasında bir harftir (sütunlara karşılık gelir), bu gösterimi kullanmak için [satır] [col] koordinatlarımızı eşlememiz gerekir
    # orijinal satranç oyununda kullanılanlarla eşleştirmek için
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_square, end_square, board, is_enpassant_move=False, is_castle_move=False):
        self.start_row = start_square[0]
        self.start_col = start_square[1]
        self.end_row = end_square[0]
        self.end_col = end_square[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        # piyon terfisi
        self.is_pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or (
                self.piece_moved == "bp" and self.end_row == 7)
        # geçerken alma
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "wp" if self.piece_moved == "bp" else "bp"
        # kale hareketi
        self.is_castle_move = is_castle_move

        self.is_capture = self.piece_captured != "--"
        self.moveID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        if self.is_pawn_promotion:
            return self.getRankFile(self.end_row, self.end_col) + "Q"
        if self.is_castle_move:
            if self.end_col == 1:
                return "0-0-0"
            else:
                return "0-0"
        if self.is_enpassant_move:
            return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                self.end_col) + " e.p."
        if self.piece_captured != "--":
            if self.piece_moved[1] == "p":
                return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                    self.end_col)
            else:
                return self.piece_moved[1] + "x" + self.getRankFile(self.end_row, self.end_col)
        else:
            if self.piece_moved[1] == "p":
                return self.getRankFile(self.end_row, self.end_col)
            else:
                return self.piece_moved[1] + self.getRankFile(self.end_row, self.end_col)

        # YAPILACAK Netleştirme hamleleri

    def getRankFile(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]

    def __str__(self):
        if self.is_castle_move:
            return "0-0" if self.end_col == 6 else "0-0-0"

        end_square = self.getRankFile(self.end_row, self.end_col)

        if self.piece_moved[1] == "p":
            if self.is_capture:
                return self.cols_to_files[self.start_col] + "x" + end_square
            else:
                return end_square + "Q" if self.is_pawn_promotion else end_square

        move_string = self.piece_moved[1]
        if self.is_capture:
            move_string += "x"
        return move_string + end_square
