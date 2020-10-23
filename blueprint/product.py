import base64
import uuid

from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify


from extend import *
from pojo import *
from redis_cache import redis_cache

product_dp = Blueprint("product", __name__, url_prefix="/product", template_folder="../templates/product")


@product_dp.route("/detail")
def detail():
    
    pid = request.args.get("id")
    my_uid = session.get("uid")
    product = Product.query.get(pid)
    if product is None:
        return redirect(url_for('index'))
    product.click_count = int(product.click_count) + 1
    db.session.commit()
    users = []
    images = product.images.split('@')
    
    categorys = Category.query.all()
    postUser = User.query.get(product.uid)
    
    return render_template("detail.html", product=product, categorys=categorys, users=users,
                            images=images, postUser=postUser)


@product_dp.route("/addCart", methods=['post'])
def addCart():
    pid = request.form.get("pid")
    count = request.form.get("count")
    product = Product.query.get(pid)
    if product is None:
        return redirect(url_for('index'))
    if product.counts == 0:
        return jsonify({'status': "500", 'msg': "来晚一步，商品已经售完，加入购物车失败"})
    uid = session.get('uid')
    if uid is None:
        return redirect(url_for('user.login'))
    if product is not None:
        p_flag = 0
        user = User.query.get(uid)
        for shopCart in user.shopcarts:
            if shopCart.pid == pid:
                p_flag = p_flag + 1
                shopCart.count = (shopCart.count + int(count))
                shopCart.subTotal = float(shopCart.count) * product.new_price
                product.counts = product.counts - int(count)
                user.shop_time = datetime.now()
                db.session.commit()

        if len(user.shopcarts) == 0 or 0 == p_flag:
            id = str(uuid.uuid1()).replace('-', '')
            subTotal = product.new_price * float(count)
            shop_cart = ShopCart(id=id, count=count, uid=uid, pid=pid, subTotal=subTotal)
            db.session.add(shop_cart)
            product.counts = product.counts - int(count)
            user.shop_time = datetime.now()
            db.session.commit()
        return jsonify({'status': '200'})
    else:
        return jsonify({'status': '500', "msg": "出现错误"})


@product_dp.route("/clear_cart")
def clear_cart():
    uid = session.get('uid')
    user = User.query.get(uid)
    if uid is not None:
        flag = request.args.get('flag')
        if flag is not None:
            if flag == "1":
                clearCart(user)
            else:
                sp_id = request.args.get('sp_id')
                if sp_id is not None:
                    shopCart = ShopCart.query.get(sp_id)
                    if shopCart is not None:
                        if shopCart.pid is not None:
                            product = Product.query.get(shopCart.pid)
                            product.counts = product.counts + shopCart.count
                        db.session.delete(shopCart)
                        db.session.commit()
                        if len(user.shopcarts) == 0:
                            user.shop_time = None
                            db.session.commit()
        else:
            clearCart(user)
    return jsonify()


def clearCart(user):
    for shopCart in user.shopcarts:
        if shopCart.pid is not None:
            product = Product.query.get(shopCart.pid)
            product.counts = product.counts + shopCart.count
        db.session.delete(shopCart)
        db.session.commit()
    user.shop_time = None

    db.session.commit()




@product_dp.route("/change_nums")
def change_nums():
    uid = session.get('uid')
    if uid is None:
        return redirect(url_for('user.login'))
    else:
        user = User.query.get(uid)
        nums = request.args.get('nums')

        sp_id = request.args.get('sp_id')
        shopCart = ShopCart.query.get(sp_id)
        if shopCart.pid is None:
            return jsonify({'error': "1"})
        all_count = shopCart.product.counts + shopCart.count
        if int(nums) > all_count:
            shopCart.count = all_count
            shopCart.subTotal = float(shopCart.count) * shopCart.product.new_price
            shopCart.product.counts = 0

            db.session.commit()
            length = 0
            for shopCart1 in user.shopcarts:
                length += shopCart1.count
            return jsonify({"error": "2", "maxlen": shopCart.count, "max_length": length})
        if shopCart is not None:
            if str.isdigit(nums):
                shopCart.count = int(nums)
                shopCart.subTotal = float(shopCart.count) * shopCart.product.new_price
                shopCart.product.counts = all_count - int(nums)

                db.session.commit()
                length = 0
                for shopCart1 in user.shopcarts:
                    length += shopCart1.count
                return jsonify({"error": '0', "max_length": length})

    return jsonify({"error": "1"})


@product_dp.route("/deleteOrderItem")
def deleteOrderItem():
    uid = session.get('uid')
    if uid is None:
        return redirect(url_for('index'))
    orderItem_id = request.args.get("id")
    flag = request.args.get("flag")
    orderItem = OrderItem.query.get(str(orderItem_id))
    if orderItem is not None:
        order = orderItem.order
        if orderItem.pid is not None:
            product = Product.query.get(orderItem.product.id)
            product.counts += orderItem.count
        db.session.delete(orderItem)
        db.session.commit()
        if len(order.orderItems) == 0:
            db.session.delete(order)
            db.session.commit()
            if flag is None:
                return redirect(url_for('index'))
            else:
                return redirect(url_for('user.userInfo', tab=3))
        db.session.commit()
        if flag is None:
            return redirect(url_for('user.showOrder', oid=order.id))
        else:
            return redirect(url_for('user.userInfo', tab=3))
    return redirect(url_for('index'))


@product_dp.route("/cancelOrder")
def cancelOrder():
    uid = session.get('uid')
    if uid is None:
        return jsonify({"error": "1"})
    user = User.query.get(uid)
    order_id = request.args.get("order_id")
    order = Order.query.get(str(order_id))
    if order is not None:
        if order.state != 2:
            for orderItem in order.orderItems:
                if orderItem.pid is not None:
                    product = Product.query.get(orderItem.product.id)
                    product.counts += orderItem.count
                db.session.delete(orderItem)
                db.session.commit()
        db.session.delete(order)
        db.session.commit()
        return jsonify({"error": "0"})
    return jsonify({"error": "1"})


@product_dp.route("/getClassify")
def getClassify():
    pageNum = request.args.get('pageNum')
    cid = request.args.get('cid')
    csid = request.args.get('csid')
    category = None
    categorySecond = None
    if csid is not None:
        categorySecond = CategorySecond.query.get(csid)
    if categorySecond is None or csid is None:
        categorySecond = CategorySecond()
    if cid is not None:
        category = Category.query.get(cid)
    if category is None or cid is None:
        category = Category()
    csids = []
    if pageNum is None or str.isdigit(pageNum) == False:
        pageNum = 1
    else:
        pageNum = int(pageNum) + 1
    if category is not None:
        for categorySecond_One in category.categoryseconds:
            csids.append(str(categorySecond_One.id))
        page_all = Product.query.filter(Product.csid.in_(csids), Product.is_pass == 2).order_by(
            Product.pdate.desc()).paginate(int(pageNum), 12, False)

    if csid is not None:
        page_all = Product.query.filter(Product.csid == str(csid), Product.is_pass == 2).order_by(
            Product.pdate.desc()).paginate(int(pageNum), 12, False)
    if categorySecond is None and category is None:
        page_all = Product.query.order_by(Product.pdate.desc(), Product.is_pass == 2).paginate(int(pageNum), 12, False)
    categorys = Category.query.all()
    return render_template('classify.html', categorys=categorys, products=page_all.items, currentPage=page_all.page,
                           pages=page_all.pages, categorySecond=categorySecond, category_my=category)



@product_dp.route("/getCategorySecond")
def getCategorySecond():
    cid = request.args.get("cid")
    cs_dicts = []
    categorySeconds = CategorySecond.query.filter(CategorySecond.cid == str(cid)).all()
    for categorySecond in categorySeconds:
        cs_dict = {"csid": categorySecond.id, "csname": categorySecond.csname}
        cs_dicts.append(cs_dict)
    return jsonify(cs_dicts)

